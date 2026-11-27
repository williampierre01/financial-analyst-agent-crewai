import type { Analysis } from "../services/api";
import { date, decimal, money } from "../services/format";

type Metric = NonNullable<Analysis["metrics"]>[number];
const names: Record<string, string> = {
  net_income: "Lucro informado pelo provedor",
  stockholders_equity: "Patrimônio dos acionistas",
  revenue: "Receita",
  total_debt: "Dívida total",
  price: "Cotação",
  diluted_eps: "Lucro diluído por ação",
};
const groups: Record<string, string> = {
  income_statement: "Demonstrativo de resultados",
  balance_sheet: "Balanço patrimonial",
  quote: "Cotação",
};
const priorities = [
  "ROE sobre patrimônio de encerramento",
  "Lucro informado/receita",
  "Dívida/patrimônio",
];
function result(m: Metric) {
  return m.status === "calculated" && m.value != null
    ? `${decimal(m.value)} ${m.unit}`
    : "Não calculado";
}
export default function EvidenceSummary({ metrics }: { metrics: Metric[] }) {
  if (!metrics.length) return null;
  const latest = metrics
    .map((m) => m.period_end ?? "")
    .sort()
    .at(-1);
  const highlights = priorities
    .map((name) =>
      metrics.find(
        (m) =>
          m.name === name &&
          m.period_end === latest &&
          m.status === "calculated",
      ),
    )
    .filter((m): m is Metric => !!m);
  return (
    <section
      className="panel evidence-panel"
      aria-labelledby="evidence-heading"
    >
      <div className="panel-heading">
        <div>
          <span className="eyebrow">CÁLCULOS E EVIDÊNCIAS</span>
          <h2 id="evidence-heading">Destaques dos indicadores</h2>
        </div>
      </div>
      <div className="evidence-body">
        <p>
          Calculados a partir dos dados desta consulta. Não explicam causas nem
          constituem recomendação.
        </p>
        {highlights.length ? (
          <div className="evidence-highlights">
            {highlights.map((m) => (
              <article key={m.name}>
                <h3>{m.name}</h3>
                <strong>{result(m)}</strong>
                <p>Exercício de {date(m.period_end)}</p>
                {m.note && <p>{m.note}</p>}
              </article>
            ))}
          </div>
        ) : (
          <p>
            Sem indicadores calculados para o exercício mais recente. Consulte
            os motivos abaixo.
          </p>
        )}
        <details>
          <summary>Ver cálculos, fontes e limitações</summary>
          {metrics.map((m, i) => (
            <article
              className="evidence-detail"
              key={`${m.name}-${m.period_end}-${i}`}
            >
              <h3>
                {m.name} · {date(m.period_end)}
              </h3>
              <p>
                <strong>{result(m)}</strong>
              </p>
              <p>Fórmula: {m.formula}</p>
              {m.reason && <p>Motivo: {m.reason}</p>}
              {m.note && <p>{m.note}</p>}
              <ul>
                {m.inputs.map((input, n) => (
                  <li key={n}>
                    {input ? (
                      <>
                        {names[input.indicator] ?? input.indicator}:{" "}
                        {money(input.value, input.currency)} ·{" "}
                        {groups[input.statement] ?? input.statement} ·{" "}
                        {date(input.period_end, input.statement === "quote")} ·
                        Fonte:{" "}
                        {input.source === "yfinance"
                          ? "Yahoo Finance"
                          : (input.source ?? "Não informada")}
                      </>
                    ) : (
                      "Valor necessário ausente na base."
                    )}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </details>
      </div>
    </section>
  );
}
