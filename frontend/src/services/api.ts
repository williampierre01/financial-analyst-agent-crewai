import type { components } from "../types/api.generated";

export type Analysis = components["schemas"]["AnalysisResponse"];
export type Snapshot = components["schemas"]["FinancialSnapshot"];
export type Period = components["schemas"]["StatementPeriod"];
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  signal: AbortSignal,
  body?: object,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: body ? "POST" : "GET",
    signal,
    headers: body
      ? { "Content-Type": "application/json", "X-Requested-With": "analista" }
      : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      window.dispatchEvent(new Event("analista:unauthorized"));
      throw new ApiError(
        response.status,
        "Sua sessão terminou. Entre novamente.",
      );
    }
    const message =
      response.status === 404
        ? "Esta análise expirou ou a API foi reiniciada. Inicie uma nova consulta."
        : response.status === 429
          ? "O limite de análises foi atingido. Aguarde um pouco antes de tentar novamente."
          : response.status === 422
            ? "Informe um código válido da B3, como PETR4."
            : "Não foi possível acessar o serviço de análise. Verifique se a API está em execução.";
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

export const createAnalysis = (ticker: string) =>
  request<Analysis>("/analyses", AbortSignal.timeout(20000), { ticker });
export const readAnalysis = (id: string, signal: AbortSignal) =>
  request<Analysis>(`/analyses/${encodeURIComponent(id)}`, signal);
