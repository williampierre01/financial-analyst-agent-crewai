import type { Snapshot } from "../services/api";
import { date, money } from "../services/format";

const groups = [
  {
    key: "income_statement",
    title: "Resultados",
    fields: [
      ["revenue", "Receita"],
      ["net_income", "Lucro líquido informado pelo provedor"],
      ["operating_income", "Resultado operacional"],
      ["diluted_eps", "Lucro diluído por ação"],
    ],
  },
  {
    key: "balance_sheet",
    title: "Balanço patrimonial",
    fields: [
      ["total_assets", "Ativo total"],
      ["stockholders_equity", "Patrimônio dos acionistas"],
      ["total_debt", "Dívida total"],
      ["cash", "Caixa e equivalentes"],
    ],
  },
  {
    key: "cash_flow",
    title: "Fluxo de caixa",
    fields: [
      ["operating_cash_flow", "Caixa operacional"],
      ["free_cash_flow", "Fluxo de caixa livre do provedor"],
    ],
  },
] as const;

export default function Statements({
  data,
  millions,
}: {
  data: Snapshot;
  millions: boolean;
}) {
  return (
    <div className="statements">
      {groups.map((group) => {
        const periods = data.statements[group.key];
        return (
          <div className="statement-group" key={group.key}>
            <h3>{group.title}</h3>
            <p className="scroll-hint">
              Deslize a tabela para ver todos os períodos.
            </p>
            {periods.length ? (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label={`Tabela de ${group.title}`}
              >
                <table>
                  <caption className="sr-only">
                    {group.title}: exercícios anuais.{" "}
                    {millions
                      ? "Valores em milhões, exceto valores pequenos e por ação."
                      : "Valores integrais."}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Indicador</th>
                      {periods.map((period) => (
                        <th scope="col" key={period.period_end}>
                          {date(period.period_end)}
                          <small>
                            {period.currency ?? "Moeda não informada"}
                          </small>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {group.fields.map(([originalKey, originalLabel]) => {
                      const reported =
                        originalKey === "operating_income" &&
                        data.schema_version === "3.1";
                      const key = reported
                        ? "reported_operating_income"
                        : originalKey;
                      const label = reported
                        ? "Resultado operacional reportado"
                        : originalLabel;
                      return (
                        <tr key={key}>
                          <th scope="row">
                            {label}
                            {key === "net_income" && (
                              <small>
                                Pode ser atribuível aos acionistas; não equivale
                                necessariamente ao lucro consolidado total.
                              </small>
                            )}
                            {key === "free_cash_flow" && (
                              <small>
                                Fórmula não conciliada; pode diferir da medida
                                publicada pela companhia.
                              </small>
                            )}
                            {key === "diluted_eps" && (
                              <small>Valor por ação · sem escala</small>
                            )}
                          </th>
                          {periods.map((period) => (
                            <td key={period.period_end}>
                              {money(
                                period.values[key],
                                period.currency,
                                millions &&
                                  !period.per_share_fields.includes(key),
                              )}
                              {reported &&
                                period.reported_operating_income_reference && (
                                  <small className="operating-reference">
                                    <a
                                      href={
                                        period
                                          .reported_operating_income_reference
                                          .document_url
                                      }
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      Fonte oficial ·{" "}
                                      {
                                        period
                                          .reported_operating_income_reference
                                          .document_location
                                      }
                                    </a>
                                    {" · "}
                                    {
                                      period.reported_operating_income_reference
                                        .scope
                                    }
                                  </small>
                                )}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted">
                Dados deste demonstrativo não disponíveis.
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
