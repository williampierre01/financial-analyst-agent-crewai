import { initializeApp } from "firebase/app";
import {
  initializeAuth,
  inMemoryPersistence,
  browserPopupRedirectResolver,
  signOut,
  type Auth,
} from "firebase/auth";

export type Account = { uid: string; role: "user" | "admin"; email?: string };
export class AccessError extends Error {
  constructor(
    public code: string,
    public status: number,
  ) {
    super("Não foi possível confirmar o acesso.");
  }
}

export async function authRequest<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(`/api/auth/${path}`, {
    method: body ? "POST" : "GET",
    credentials: "same-origin",
    headers: body
      ? { "Content-Type": "application/json", "X-Requested-With": "analista" }
      : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(20000),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new AccessError(data.detail?.code ?? "unavailable", response.status);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

let client: Promise<Auth> | undefined;
let initializedClient: Auth | undefined;
export async function clearFirebaseIdentity() {
  if (initializedClient) await signOut(initializedClient);
}
export function firebaseAuth() {
  client ??= authRequest<{
    apiKey: string;
    authDomain: string;
    projectId: string;
  }>("config")
    .then(
      (config) =>
        (initializedClient = initializeAuth(initializeApp(config), {
          persistence: inMemoryPersistence,
          popupRedirectResolver: browserPopupRedirectResolver,
        })),
    )
    .catch((error) => {
      client = undefined;
      throw error;
    });
  return client;
}

export function clearPrivateState() {
  try {
    for (const key of Object.keys(sessionStorage)) {
      if (key.startsWith("analista.active-analysis"))
        sessionStorage.removeItem(key);
    }
  } catch {
    /* Browser storage may be disabled. */
  }
}

export const accountTabId = crypto.randomUUID();
export function notifyAccountChange() {
  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel("analista-account");
    channel.postMessage(accountTabId);
    channel.close();
  }
}
