// Only fixed messages are shown; never expose Firebase payloads or credentials.
export function mfaFailure(error: unknown) {
  const code = (error as { code?: string } | null)?.code;
  switch (code) {
    case "auth/invalid-verification-code":
      return {
        retry: true,
        message:
          "O código do autenticador não foi aceito. Aguarde o próximo código, confira se está usando a entrada Analista criada com esta chave e mantenha a data e a hora automáticas no celular. Tente novamente nesta tela.",
      };
    case "auth/code-expired":
    case "auth/session-expired":
    case "auth/invalid-multi-factor-session":
    case "auth/missing-multi-factor-session":
    case "auth/requires-recent-login":
    case "auth/user-token-expired":
      return {
        retry: false,
        message:
          "A sessão de confirmação expirou. Entre novamente. Se aparecer uma nova chave de configuração, use essa nova chave no autenticador.",
      };
    case "auth/too-many-requests":
      return {
        retry: false,
        message:
          "O Firebase limitou as tentativas de confirmação. Aguarde antes de entrar novamente.",
      };
    case "auth/network-request-failed":
      return {
        retry: false,
        message:
          "A conexão foi interrompida durante a confirmação. Entre novamente para verificar se o autenticador já foi cadastrado.",
      };
    case "auth/operation-not-allowed":
      return {
        retry: false,
        message:
          "O Firebase não permitiu confirmar o autenticador. O administrador precisa verificar a configuração de autenticação em duas etapas. Referência: MFA_OPERATION_NOT_ALLOWED.",
      };
    default:
      return {
        retry: false,
        message:
          "Não foi possível concluir a confirmação do autenticador. Entre novamente. Se persistir, contate o administrador. Referência: MFA_CONFIRMATION_FAILED.",
      };
  }
}
