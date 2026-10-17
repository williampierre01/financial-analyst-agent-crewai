import { useState, type FormEvent } from "react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  ChartNoAxesCombined,
  Check,
  Database,
  FileText,
  Info,
  Layers,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Statements from "./components/Statements";
import { useAnalysis } from "./services/useAnalysis";
import { date, money } from "./services/format";
import { reportMarkdown } from "./services/reportMarkdown";
import { reportPresentation } from "./services/reportPresentation";
import type { Snapshot } from "./services/api";

const steps = [
  "Coletando dados",
  "Analisando indicadores",
  "Preparando interpretação",
];
const quality = {
  complete: "Base disponível",
  partial: "Dados parciais",
  unavailable: "Dados indisponíveis",
};

function Metric({
  label,
  value,
  detail,
  highlight = false,
}: {
  label: string;
  value: string;
  detail: string;
  highlight?: boolean;
}) {
  return (
    <article className={`metric ${highlight ? "metric-highlight" : ""}`}>
      <div className="metric-label">
        {label}
        {highlight && <Activity size={17} aria-hidden="true" />}
      </div>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}
function annualMetric(
  data: Snapshot | null | undefined,
  group: keyof Snapshot["statements"],
  field: string,
) {
  const periods = data?.statements[group];
  const period =
    periods?.find((p) => p.period_end === data?.common_period) ?? periods?.[0];
  return {
    value: period ? money(period.values[field], period.currency, true) : "—",
    detail: period
      ? `Exercício de ${date(period.period_end)}${period.currency ? "" : " · moeda não informada"}`
      : "Aguardando consulta",
  };
}

export default function App() {
  const [ticker, setTicker] = useState("");
  const [validation, setValidation] = useState("");
  const [millions, setMillions] = useState(true);
  const { analysis, error, paused, start, resume, reset, busy, starting } =
    useAnalysis();
  const data = analysis?.data;
  const revenue = annualMetric(data, "income_statement", "revenue");
  const profit = annualMetric(data, "income_statement", "net_income");
  const cash = annualMetric(data, "cash_flow", "free_cash_flow");
  const stageIndex =
    analysis?.stage === "quant" ? 1 : analysis?.stage === "cio" ? 2 : 0;
  async function submit(event: FormEvent) {
    event.preventDefault();
    const normalized = ticker.trim().toUpperCase().replace(/\.SA$/, "");
    if (!/^[A-Z]{4}[0-9]{1,2}$/.test(normalized)) {
      setValidation("Informe um código da B3, como PETR4, VALE3 ou ITUB4.");
      return;
    }
    setValidation("");
    setTicker(normalized);
    await start(normalized);
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#conteudo">
        Ir para o conteúdo
      </a>
      <aside className="sidebar">
        <a className="brand" href="#consulta">
          <span className="brand-mark">
            <ChartNoAxesCombined size={24} />
          </span>
          <span>
            analista<span className="brand-sub">AÇÕES BRASILEIRAS</span>
          </span>
        </a>
        <div className="sidebar-section">ÁREA DE ANÁLISE</div>
        <nav aria-label="Navegação principal">
          <a className="nav-current" href="#consulta">
            <Layers size={18} />
            Visão geral
            <ArrowUpRight size={15} />
          </a>
          <a href="#demonstrativos">
            <Database size={18} />
            Demonstrativos
          </a>
          <a href="#interpretacao">
            <Sparkles size={18} />
            Interpretação
          </a>
        </nav>
        <div className="sidebar-note">
          <span className="small-icon">
            <ShieldCheck size={19} />
          </span>
          <h3>Dados com contexto.</h3>
          <p>Fonte, período e limitações acompanham cada consulta.</p>
          <a href="#metodologia">
            Entenda a análise <ArrowUpRight size={14} />
          </a>
        </div>
        <div className="sidebar-footer">
          <span className="country-mark">BR</span>
          <div>
            Mercado brasileiro<small>Fonte: Yahoo Finance</small>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            Pesquisa de ações <span className="separator">/</span>{" "}
            <strong>Visão geral</strong>
          </span>
          <span className="market-tag">
            <span /> B3 · Brasil
          </span>
        </header>
        <main id="conteudo">
          <section className="hero" id="consulta">
            <div>
              <div className="eyebrow">ANÁLISE FUNDAMENTALISTA</div>
              <h1>
                Os números por trás
                <br />
                da sua próxima análise<span>.</span>
              </h1>
              <p>
                Explore os fundamentos de uma ação brasileira.
                <br className="desktop-break" /> Dados organizados, fontes
                claras e uma leitura assistida por IA.
              </p>
            </div>
            <div className="hero-stamp" aria-hidden="true">
              <ChartNoAxesCombined size={55} strokeWidth={1} />
              <span>
                INFORMAÇÃO
                <br />
                ANTES DA DECISÃO
              </span>
            </div>
          </section>
          <section className="search-panel" aria-label="Consultar uma ação">
            <form onSubmit={submit} noValidate>
              <div className="search-field">
                <label htmlFor="ticker">Qual ação vamos analisar?</label>
                <div
                  className={`input-wrap ${validation ? "input-invalid" : ""}`}
                >
                  <Search size={20} aria-hidden="true" />
                  <input
                    id="ticker"
                    value={ticker}
                    onChange={(event) => {
                      setTicker(event.target.value);
                      setValidation("");
                    }}
                    placeholder="Digite o código, ex.: PETR4"
                    maxLength={16}
                    autoComplete="off"
                    spellCheck={false}
                    disabled={busy}
                    aria-invalid={!!validation}
                    aria-describedby={
                      validation ? "ticker-error" : "ticker-hint"
                    }
                  />
                  <span className="input-market">B3</span>
                </div>
              </div>
              <button className="primary" type="submit" disabled={busy}>
                {busy ? (
                  <>
                    <LoaderCircle className="spin" size={18} />
                    {starting ? "Iniciando…" : "Analisando…"}
                  </>
                ) : (
                  <>
                    Analisar ação <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>
            {validation && (
              <p className="field-error" id="ticker-error" role="alert">
                {validation}
              </p>
            )}
            <div className="search-meta">
              <div className="examples">
                <span id="ticker-hint">Experimente</span>
                {["PETR4", "VALE3", "ITUB4"].map((code) => (
                  <button
                    key={code}
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      setTicker(code);
                      setValidation("");
                      document.getElementById("ticker")?.focus();
                    }}
                  >
                    {code}
                  </button>
                ))}
              </div>
              <span className="source-note">
                <Database size={13} /> Yahoo Finance · disponibilidade variável
              </span>
            </div>
          </section>
          {error && (
            <div className="notice error" role="alert">
              <TriangleAlert size={19} />
              <div>
                <strong>
                  {paused
                    ? "Acompanhamento pausado"
                    : "Não foi possível concluir esta operação"}
                </strong>
                <p>{error}</p>
                {paused && (
                  <div className="notice-actions">
                    <button onClick={resume}>Retomar acompanhamento</button>
                    <button onClick={reset}>Iniciar outra consulta</button>
                    <small>
                      Uma nova consulta não cancela a análise anterior.
                    </small>
                  </div>
                )}
              </div>
            </div>
          )}
          {busy && !paused && (
            <section
              className="progress-panel"
              aria-label="Andamento da análise"
            >
              <div className="progress-title" role="status">
                <LoaderCircle className="spin" size={17} />
                <strong>{steps[stageIndex]}</strong>
                <span>
                  {data
                    ? data.status === "unavailable"
                      ? "Coleta concluída sem dados financeiros disponíveis."
                      : "Dados disponíveis abaixo. A interpretação está em andamento."
                    : "Os dados aparecerão assim que estiverem disponíveis."}
                </span>
              </div>
              <ol>
                {steps.map((label, index) => (
                  <li
                    key={label}
                    className={index <= stageIndex ? "active" : ""}
                    aria-current={index === stageIndex ? "step" : undefined}
                  >
                    <span>
                      {index < stageIndex ? <Check size={12} /> : index + 1}
                    </span>
                    {label}
                  </li>
                ))}
              </ol>
            </section>
          )}
          <section className="overview" aria-labelledby="overview-heading">
            <div className="section-heading">
              <div>
                <div className="eyebrow">PANORAMA FINANCEIRO</div>
                <h2 id="overview-heading">
                  {data ? (
                    <>
                      {data.display_ticker}
                      <span className="ticker-exchange">B3</span>
                    </>
                  ) : (
                    "Seu ponto de partida"
                  )}
                </h2>
              </div>
              {data ? (
                <span className={`quality ${data.status}`}>
                  <span />
                  {quality[data.status]}
                </span>
              ) : (
                <span className="subtle-label">Aguardando sua consulta</span>
              )}
            </div>
            <div className="metrics">
              <Metric
                label="Cotação informada"
                value={
                  data
                    ? money(data.quote?.price, data.quote?.currency ?? null)
                    : "—"
                }
                detail={
                  data?.quote
                    ? `${date(data.quote.as_of, true)}${data.quote.as_of ? " · Brasília" : " pela fonte"}`
                    : "Preço não disponível"
                }
                highlight
              />
              <Metric label="Receita anual" {...revenue} />
              <Metric label="Lucro líquido anual" {...profit} />
              <Metric label="Fluxo de caixa livre anual" {...cash} />
            </div>
            {data && (
              <div className="provenance">
                <span>
                  Consultado em <strong>{date(data.retrieved_at, true)}</strong>{" "}
                  · Brasília
                </span>
                <span>
                  {data.quote?.freshness === "recent"
                    ? "Cotação dentro do critério de atualidade"
                    : "Cotação antiga, ausente ou sem data confirmada"}{" "}
                  · Não é tempo real
                </span>
              </div>
            )}
          </section>
          {data && (data.warnings.length > 0 || data.status !== "complete") && (
            <div className="notice warning">
              <TriangleAlert size={20} />
              <div>
                <strong>O que considerar ao ler estes dados</strong>
                {data.warnings.length ? (
                  <ul>
                    {data.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    A base não atende a todos os critérios de disponibilidade.
                    Observe os campos ausentes antes de interpretar os
                    resultados.
                  </p>
                )}
              </div>
            </div>
          )}
          <div className="detail-layout">
            <section
              className="panel financial-panel"
              id="demonstrativos"
              aria-labelledby="statements-heading"
            >
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">DADOS DA EMPRESA</span>
                  <h2 id="statements-heading">Demonstrativos financeiros</h2>
                </div>
                <FileText size={20} className="muted" />
              </div>
              <div className="table-toolbar">
                <span>Exercícios anuais · moeda indicada pela fonte</span>
                <label className="scale-control">
                  <span className="sr-only">Escala dos valores</span>
                  <select
                    value={millions ? "millions" : "full"}
                    onChange={(event) =>
                      setMillions(event.target.value === "millions")
                    }
                  >
                    <option value="millions">Em milhões</option>
                    <option value="full">Valores integrais</option>
                  </select>
                </label>
              </div>
              {data ? (
                <Statements data={data} millions={millions} />
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Database size={26} strokeWidth={1.4} />
                  </div>
                  <h3>Uma base para olhar mais longe</h3>
                  <p>
                    Consulte uma ação para comparar resultados,
                    <br />
                    patrimônio e geração de caixa entre exercícios.
                  </p>
                  <div className="empty-labels">
                    <span>Resultados</span>
                    <span>Patrimônio</span>
                    <span>Caixa</span>
                  </div>
                </div>
              )}
              <div className="table-footnote">
                <Info size={14} />
                <span>
                  Valores pequenos e lucro por ação sem escala. Ausências não
                  são zero. Sem conversão cambial.
                </span>
              </div>
            </section>
            <section
              className="panel interpretation-panel"
              id="interpretacao"
              aria-labelledby="interpretation-heading"
            >
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">CONTEXTO PARA OS NÚMEROS</span>
                  <h2 id="interpretation-heading">Leitura da análise</h2>
                </div>
                <span className="ai-icon">
                  <Sparkles size={19} />
                </span>
              </div>
              {analysis?.interpretation ? (
                <div className="markdown">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, reportPresentation]}
                    skipHtml
                    components={{
                      table: ({ children }) => (
                        <div
                          className="table-scroll"
                          tabIndex={0}
                          role="region"
                          aria-label="Tabela da interpretação — role para ver todas as colunas"
                        >
                          <table>{children}</table>
                        </div>
                      ),
                      pre: ({ children }) => <pre tabIndex={0}>{children}</pre>,
                      a: (props) => (
                        <a
                          href={props.href}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {props.children}
                          <span className="sr-only"> (abre em outra aba)</span>
                        </a>
                      ),
                    }}
                  >
                    {reportMarkdown(analysis.interpretation)}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="interpretation-empty">
                  <Sparkles size={29} strokeWidth={1.3} />
                  <h3>
                    {analysis?.interpretation_status === "failed"
                      ? "Interpretação indisponível"
                      : analysis?.interpretation_status === "skipped"
                        ? "Sem base para interpretar"
                        : busy
                          ? "Preparando uma leitura dos dados"
                          : "Os dados contam uma história."}
                  </h3>
                  <p>
                    {analysis?.interpretation_status === "failed"
                      ? "Os dados financeiros continuam disponíveis. Confira a configuração dos serviços de IA antes de uma nova análise."
                      : analysis?.interpretation_status === "skipped"
                        ? "Não foi possível obter dados suficientes para iniciar a interpretação."
                        : busy
                          ? "A interpretação aparecerá aqui ao terminar. Você já pode consultar os dados disponíveis."
                          : "Após a consulta, a IA organiza os resultados, as notícias e as limitações da análise neste espaço."}
                  </p>
                </div>
              )}
              {!!analysis?.errors.length && (
                <div className="analysis-errors">
                  {analysis.errors.map((issue, index) => (
                    <p key={index}>{issue.message}</p>
                  ))}
                </div>
              )}
              <div className="ai-note">
                <ShieldCheck size={15} />
                <span>
                  Interpretação assistida por IA. Confira os dados e as fontes
                  antes de tomar decisões.
                </span>
              </div>
            </section>
          </div>
          <details className="methodology" id="metodologia">
            <summary>
              <Info size={16} />
              Como ler esta análise
            </summary>
            <p>
              A fonte financeira é o Yahoo Finance. A situação da base considera
              presença de campos essenciais, moedas e períodos compatíveis.
              “Base disponível” indica validação automática, não auditoria dos
              demonstrativos oficiais.
            </p>
            <p>
              O critério de atualidade aceita cotações de até 7 dias e
              demonstrativos de até 550 dias. Os cartões mostram o período comum
              quando disponível; caso contrário, exibem o exercício mais recente
              de cada demonstrativo, com a respectiva data. As moedas não são
              convertidas.
            </p>
            <p>
              As análises ficam temporariamente no servidor e são perdidas se
              ele reiniciar. Acompanhamento interrompido não significa
              cancelamento da análise.
            </p>
          </details>
          <footer className="page-footer">
            <span>
              <ChartNoAxesCombined size={16} /> analista{" "}
              <span className="footer-dot">·</span> Ações brasileiras
            </span>
            <p>
              Demonstração técnica. Não constitui recomendação de investimento.
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}
