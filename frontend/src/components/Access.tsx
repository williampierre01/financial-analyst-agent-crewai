import { useEffect, useState, type FormEvent } from "react";
import {
  signInWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  sendPasswordResetEmail,
  sendEmailVerification,
  getMultiFactorResolver,
  multiFactor,
  TotpMultiFactorGenerator,
  type MultiFactorError,
  type MultiFactorResolver,
  type TotpSecret,
  type User,
} from "firebase/auth";
import App from "../App";
import {
  AccessError,
  authRequest,
  clearPrivateState,
  clearFirebaseIdentity,
  firebaseAuth,
  notifyAccountChange,
  accountTabId,
  type Account,
} from "../services/auth";

export default function Access() {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [resolver, setResolver] = useState<MultiFactorResolver | null>(null);
  const [enrollUser, setEnrollUser] = useState<User | null>(null);
  const [secret, setSecret] = useState<TotpSecret | null>(null);
  const [logoutPending, setLogoutPending] = useState(false);
  const [cleanupFailed, setCleanupFailed] = useState(false);

  async function discardTemporaryLogin() {
    setSecret(null);
    setEnrollUser(null);
    setResolver(null);
    setCode("");
    setPassword("");
    try {
      await clearFirebaseIdentity();
    } catch {
      setCleanupFailed(true);
    }
  }

  useEffect(() => {
    let live = true;
    authRequest<Account>("me")
      .then((user) => {
        if (live) setAccount(user);
      })
      .catch((error) => {
        if (live && !(error instanceof AccessError && error.status === 401))
          setMessage(
            "Acesso temporariamente indisponível. Tente novamente mais tarde.",
          );
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    const expire = () => {
      live = false;
      setLoading(false);
      setAccount(null);
      clearPrivateState();
      setMessage("Sua sessão terminou. Entre novamente.");
    };
    window.addEventListener("analista:unauthorized", expire);
    const channel =
      typeof BroadcastChannel === "undefined"
        ? null
        : new BroadcastChannel("analista-account");
    if (channel)
      channel.onmessage = (event) => {
        if (event.data !== accountTabId) expire();
      };
    return () => {
      live = false;
      window.removeEventListener("analista:unauthorized", expire);
      channel?.close();
    };
  }, []);

  async function establish(user: User) {
    if (!user.emailVerified) {
      try {
        await sendEmailVerification(user);
      } finally {
        await clearFirebaseIdentity();
      }
      setMessage(
        "Confirme seu e-mail pelo link enviado e entre novamente. Confira também a pasta de spam.",
      );
      return;
    }
    try {
      const next = await authRequest<Account>("session", {
        id_token: await user.getIdToken(true),
      });
      await clearFirebaseIdentity();
      clearPrivateState();
      notifyAccountChange();
      setAccount(next);
      setPassword("");
      setCode("");
      setResolver(null);
      setSecret(null);
      setEnrollUser(null);
      setMessage("");
    } catch (error) {
      if (error instanceof AccessError && error.code === "mfa_required") {
        if (multiFactor(user).enrolledFactors.length) {
          await clearFirebaseIdentity();
          setMessage(
            "Entre novamente e confirme o código do seu autenticador.",
          );
        } else {
          const enrollmentSecret =
            await TotpMultiFactorGenerator.generateSecret(
              await multiFactor(user).getSession(),
            );
          setEnrollUser(user);
          setSecret(enrollmentSecret);
          setMessage(
            "Sua conta administrativa precisa de autenticação em duas etapas.",
          );
        }
      } else {
        await clearFirebaseIdentity();
        throw error;
      }
    }
  }

  async function login(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const auth = await firebaseAuth();
      if (secret && enrollUser) {
        await multiFactor(enrollUser).enroll(
          TotpMultiFactorGenerator.assertionForEnrollment(secret, code),
          "Autenticador",
        );
        await signOut(auth);
        setSecret(null);
        setEnrollUser(null);
        setCode("");
        setPassword("");
        setMessage(
          "Autenticador cadastrado. Entre novamente pelo método escolhido e confirme o código para concluir.",
        );
      } else if (resolver) {
        const hint = resolver.hints.find(
          (item) => item.factorId === TotpMultiFactorGenerator.FACTOR_ID,
        );
        if (!hint) throw new Error("Unsupported factor");
        const result = await resolver.resolveSignIn(
          TotpMultiFactorGenerator.assertionForSignIn(hint.uid, code),
        );
        await establish(result.user);
      } else {
        try {
          const result = await signInWithEmailAndPassword(
            auth,
            email,
            password,
          );
          await establish(result.user);
        } catch (error) {
          if (
            (error as { code?: string }).code ===
            "auth/multi-factor-auth-required"
          ) {
            setResolver(
              getMultiFactorResolver(auth, error as MultiFactorError),
            );
            setPassword("");
            setMessage("Digite o código do seu aplicativo autenticador.");
          } else throw error;
        }
      }
    } catch (error) {
      await discardTemporaryLogin();
      setMessage(
        error instanceof AccessError && error.status === 403
          ? "Esta conta não tem acesso autorizado. Contate o administrador."
          : "Não foi possível entrar. Confira os dados ou aguarde antes de tentar novamente.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function recover() {
    if (!email.trim()) {
      setMessage("Informe seu e-mail para recuperar o acesso.");
      return;
    }
    setBusy(true);
    try {
      await sendPasswordResetEmail(await firebaseAuth(), email);
    } catch {
      /* Same message whether an address exists, is blocked or is unknown. */
    } finally {
      setMessage(
        "Se houver uma conta elegível, você receberá instruções por e-mail. Confira o spam; se não receber, aguarde ou contate o administrador.",
      );
      setBusy(false);
    }
  }

  async function loginGoogle() {
    setBusy(true);
    setMessage("");
    setPassword("");
    try {
      const auth = await firebaseAuth();
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: "select_account" });
      try {
        const result = await signInWithPopup(auth, provider);
        await establish(result.user);
      } catch (error) {
        if (
          (error as { code?: string }).code ===
          "auth/multi-factor-auth-required"
        ) {
          setResolver(getMultiFactorResolver(auth, error as MultiFactorError));
          setMessage("Digite o código do seu aplicativo autenticador.");
        } else throw error;
      }
    } catch (error) {
      await discardTemporaryLogin();
      const errorCode = (error as { code?: string }).code;
      if (
        errorCode === "auth/popup-closed-by-user" ||
        errorCode === "auth/cancelled-popup-request"
      ) {
        setMessage("Login cancelado. Você pode tentar novamente.");
      } else if (errorCode === "auth/popup-blocked") {
        setMessage("Permita a janela de login neste site e tente novamente.");
      } else if (
        errorCode === "auth/account-exists-with-different-credential"
      ) {
        setMessage(
          "Use o método original desta conta. Se necessário, recupere sua senha ou contate o administrador para vincular o acesso.",
        );
      } else {
        setMessage(
          error instanceof AccessError && error.status === 403
            ? "Esta conta não tem acesso autorizado. Contate o administrador."
            : "Não foi possível entrar com Google. Tente novamente ou contate o administrador.",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    setBusy(true);
    setAccount(null);
    clearPrivateState();
    notifyAccountChange();
    setLogoutPending(true);
    try {
      await authRequest("logout", {});
      setLogoutPending(false);
      setMessage("Você saiu da conta.");
    } catch {
      setMessage(
        "A tela foi bloqueada, mas não foi possível confirmar a saída no servidor. Tente concluir a saída.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    setBusy(true);
    try {
      await discardTemporaryLogin();
    } finally {
      setSecret(null);
      setEnrollUser(null);
      setResolver(null);
      setCode("");
      setPassword("");
      setBusy(false);
    }
  }

  if (loading)
    return (
      <main className="access-page">
        <p role="status">Verificando acesso…</p>
      </main>
    );
  if (cleanupFailed)
    return (
      <main className="access-page">
        <p role="alert">
          Não foi possível concluir a limpeza do login. Recarregue a página para
          tentar novamente.
        </p>
        <button onClick={() => window.location.reload()}>
          Recarregar página
        </button>
      </main>
    );
  if (account)
    return (
      <>
        <div className="account-bar">
          <span>
            {account.email || "Conta conectada"} ·{" "}
            {account.role === "admin" ? "Administrador" : "Usuário"}
          </span>
          <button onClick={logout} disabled={busy}>
            Sair da conta
          </button>
        </div>
        <App key={account.uid} uid={account.uid} />
      </>
    );
  return (
    <main className="access-page">
      <section className="access-card" aria-labelledby="access-title">
        <p className="access-brand">analista · Ações brasileiras</p>
        <h1 id="access-title">Entre para acessar suas análises</h1>
        <p>
          Informações com contexto para apoiar suas decisões. Acesso disponível
          para usuários convidados.
        </p>
        {message && (
          <p role="status" className="access-message">
            {message}
          </p>
        )}
        {logoutPending ? (
          <button onClick={logout} disabled={busy}>
            Concluir saída
          </button>
        ) : (
          <form onSubmit={login}>
            {!resolver && !secret && (
              <>
                <button
                  type="button"
                  className="access-secondary"
                  onClick={loginGoogle}
                  disabled={busy}
                >
                  Entrar com Google
                </button>
                <p>Ou entre com e-mail e senha</p>
                <label htmlFor="access-email">E-mail</label>
                <input
                  id="access-email"
                  type="email"
                  autoComplete="username"
                  required
                  maxLength={254}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={busy}
                />
                <label htmlFor="access-password">Senha</label>
                <input
                  id="access-password"
                  type="password"
                  autoComplete="current-password"
                  required
                  maxLength={4096}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  disabled={busy}
                />
              </>
            )}
            {secret && (
              <div>
                <p>
                  No aplicativo autenticador, adicione uma conta por chave de
                  configuração. Não compartilhe esta chave:
                </p>
                <code className="totp-secret">{secret.secretKey}</code>
                <p>Depois, informe o código de seis dígitos.</p>
              </div>
            )}
            {(resolver || secret) && (
              <>
                <label htmlFor="access-code">Código do autenticador</label>
                <input
                  id="access-code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                  disabled={busy}
                />
              </>
            )}
            <button type="submit" disabled={busy}>
              {busy ? "Aguarde…" : secret ? "Confirmar autenticador" : "Entrar"}
            </button>
            {!resolver && !secret ? (
              <button
                type="button"
                className="access-secondary"
                onClick={recover}
                disabled={busy}
              >
                Esqueci minha senha / Primeiro acesso
              </button>
            ) : (
              <button
                type="button"
                className="access-secondary"
                onClick={cancel}
                disabled={busy}
              >
                Voltar ao login
              </button>
            )}
          </form>
        )}
        <p className="access-note">
          Seu acesso é individual. Nunca compartilhe sua senha ou códigos de
          verificação.
        </p>
      </section>
    </main>
  );
}
