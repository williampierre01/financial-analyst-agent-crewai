export const decimal = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
export function date(value: string | null | undefined, time = false) {
  if (!value) return "Não informada";
  const parsed = new Date(value.length === 10 ? `${value}T12:00:00Z` : value);
  if (Number.isNaN(parsed.getTime())) return "Não informada";
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(time ? ({ hour: "2-digit", minute: "2-digit" } as const) : {}),
  }).format(parsed);
}
export function money(
  value: number | null | undefined,
  currency: string | null,
  millions = false,
) {
  if (value == null || !Number.isFinite(value)) return "Não disponível";
  const scaled = millions && (value === 0 || Math.abs(value) >= 10000);
  return `${currency === "BRL" ? "R$" : (currency ?? "Moeda não informada")} ${decimal(scaled ? value / 1e6 : value)}${scaled ? " mi" : ""}`;
}
