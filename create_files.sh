#!/usr/bin/env bash
set -e

cat > requirements.txt << 'FILE_EOF'
# --- Orquestração / MCP (usadas nas Etapas 2 e 3, já deixamos fixado) ---
crewai>=0.140.0
crewai-tools[mcp]>=0.50.0
mcp>=1.9.0

# --- Servidor MCP (Etapa 1) ---
pydantic>=2.7.0
yfinance>=0.2.60
pandas-datareader>=0.10.0
ddgs>=9.0.0          # NAO instalar duckduckgo-search, foi renomeado/deprecado
tenacity>=8.3.0
python-dotenv>=1.0.1

# --- LLM providers (Etapa 2) ---
# um unico cliente 'openai' cobre DeepSeek e Groq -- ambos sao OpenAI-compatible,
# so muda base_url e api_key (ver llm_provider.py)
openai>=1.30.0

# --- UI (Etapa 3) ---
gradio>=4.40.0
FILE_EOF

cat > .gitignore << 'FILE_EOF'
__pycache__/
*.pyc
.venv/
venv/
.env
*.egg-info/
.DS_Store
FILE_EOF

cat > mcp_server.py << 'FILE_EOF'
"""
Servidor MCP (stdio) para o pipeline de analise financeira autonoma.

Expoe duas tools:
  - get_financial_statements(ticker): fundamentos (DRE, balanco, fluxo de caixa)
    + cotacao atual. Fundamentos vem exclusivamente do yfinance (nao existe
    fallback gratuito equivalente para DRE/Balanco -- o Stooq so tem
    historico de preco). A cotacao atual, essa sim, tem fallback no Stooq.
  - get_market_news(ticker): noticias recentes via ddgs.

Toda saida e validada contra um schema Pydantic antes de retornar. Se a
validacao falhar, a tool retorna um erro estruturado em vez de deixar dado
malformado vazar pro agente seguinte.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf
from ddgs import DDGS
from mcp.server.fastmcp import FastMCP
from pandas_datareader import data as pdr
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("financial-analyst-tools")


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class Quote(BaseModel):
    price: float
    currency: str = "USD"
    source: str = Field(description="'yfinance' ou 'stooq' (fallback)")
    as_of: datetime


class FinancialStatements(BaseModel):
    ticker: str
    quote: Optional[Quote] = None
    income_statement: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    balance_sheet: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    cash_flow: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    fundamentals_available: bool = Field(
        description="False se o yfinance falhou -- nesse caso nao ha fallback "
        "gratuito para DRE/Balanco, so para cotacao."
    )
    warning: Optional[str] = None


class NewsItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str = ""


class MarketNews(BaseModel):
    ticker: str
    items: list[NewsItem] = Field(default_factory=list)


class ToolError(BaseModel):
    error: str
    ticker: str


# --------------------------------------------------------------------------- #
# Helpers com retry
# --------------------------------------------------------------------------- #

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _fetch_yfinance(ticker: str) -> yf.Ticker:
    t = yf.Ticker(ticker)
    # forca uma chamada real pra estourar a exception aqui se o ticker
    # estiver invalido ou o yfinance estiver bloqueado, em vez de mais tarde
    info = t.fast_info
    if info is None:
        raise ValueError(f"yfinance nao retornou dados para {ticker}")
    return t


def _df_to_nested_dict(df) -> dict[str, dict[str, float | None]]:
    """Converte um DataFrame do yfinance (linhas=conta, colunas=periodo)
    em dict serializavel: {periodo_iso: {conta: valor}}."""
    if df is None or df.empty:
        return {}
    out: dict[str, dict[str, float | None]] = {}
    for col in df.columns:
        period_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        out[period_key] = {
            str(idx): (float(val) if val == val else None)  # val==val descarta NaN
            for idx, val in df[col].items()
        }
    return out


def _fetch_stooq_price(ticker: str) -> Optional[Quote]:
    """Fallback de cotacao. Stooq NAO tem DRE/Balanco, so preco historico."""
    try:
        df = pdr.DataReader(ticker, "stooq")
        if df is None or df.empty:
            return None
        last_row = df.sort_index().iloc[-1]
        return Quote(
            price=float(last_row["Close"]),
            currency="USD",
            source="stooq",
            as_of=datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallback Stooq tambem falhou para %s: %s", ticker, exc)
        return None


# --------------------------------------------------------------------------- #
# Tools MCP
# --------------------------------------------------------------------------- #

@mcp.tool()
def get_financial_statements(ticker: str) -> dict:
    """Retorna DRE, Balanco, Fluxo de Caixa e cotacao atual para um ticker.

    Fundamentos vem do yfinance. Se o yfinance falhar completamente, a tool
    ainda tenta obter a cotacao via Stooq (fallback), mas retorna
    fundamentals_available=False -- nao existe fallback gratuito para
    demonstrativos financeiros.
    """
    try:
        t = _fetch_yfinance(ticker)
        # fast_info nao e um dict comum -- acesso por atributo e o caminho
        # confiavel entre versoes do yfinance. .get("last_price") sempre
        # cai no default e mascara o preco real como 0.0 silenciosamente.
        raw_price = getattr(t.fast_info, "last_price", None)
        raw_currency = getattr(t.fast_info, "currency", None)
        quote = Quote(
            price=float(raw_price) if raw_price is not None else 0.0,
            currency=str(raw_currency) if raw_currency else "USD",
            source="yfinance",
            as_of=datetime.now(timezone.utc),
        )

        result = FinancialStatements(
            ticker=ticker,
            quote=quote,
            income_statement=_df_to_nested_dict(t.financials),
            balance_sheet=_df_to_nested_dict(t.balance_sheet),
            cash_flow=_df_to_nested_dict(t.cashflow),
            fundamentals_available=True,
        )
        return result.model_dump(mode="json")

    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance falhou para %s: %s", ticker, exc)
        fallback_quote = _fetch_stooq_price(ticker)
        result = FinancialStatements(
            ticker=ticker,
            quote=fallback_quote,
            fundamentals_available=False,
            warning=(
                f"yfinance indisponivel ({exc}). Cotacao "
                f"{'obtida via Stooq' if fallback_quote else 'tambem indisponivel'}. "
                "DRE/Balanco/Fluxo de caixa nao puderam ser recuperados."
            ),
        )
        return result.model_dump(mode="json")


@mcp.tool()
def get_market_news(ticker: str, max_results: int = 5) -> dict:
    """Retorna as noticias mais recentes relevantes para o ticker via ddgs."""
    # tickers brasileiros (.SA) tem pouco resultado com query em ingles
    # generica -- adicionar "acoes" ajuda o ddgs a achar cobertura local
    query = f"{ticker} acoes" if ticker.upper().endswith(".SA") else f"{ticker} stock"
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
        items = [
            NewsItem(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=(r.get("body", "") or "")[:300],
                source=r.get("source", ""),
            )
            for r in raw
        ]
        return MarketNews(ticker=ticker, items=items).model_dump(mode="json")

    except Exception as exc:  # noqa: BLE001
        logger.error("ddgs falhou para %s: %s", ticker, exc)
        return ToolError(error=str(exc), ticker=ticker).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
FILE_EOF

cat > test_tools.py << 'FILE_EOF'
"""
Teste manual de fumaca (smoke test) para o checkpoint da Etapa 1.
Roda as duas tools direto, sem passar pelo protocolo MCP/stdio, so pra
confirmar que os dados vem certos e que o fallback dispara quando esperado.

Uso:
    python test_tools.py PETR4.SA
    python test_tools.py AAPL
    python test_tools.py TICKER_INVALIDO_XPTO   # deve mostrar fundamentals_available=False
"""

import json
import sys

from mcp_server import get_financial_statements, get_market_news

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    print(f"\n=== get_financial_statements({ticker!r}) ===")
    fs = get_financial_statements(ticker)
    print(f"fundamentals_available: {fs['fundamentals_available']}")
    print(f"quote: {fs['quote']}")
    if fs.get("warning"):
        print(f"warning: {fs['warning']}")
    print(f"periodos de DRE encontrados: {list(fs['income_statement'].keys())}")

    print(f"\n=== get_market_news({ticker!r}) ===")
    news = get_market_news(ticker)
    if "error" in news:
        print(f"erro: {news['error']}")
    else:
        for item in news["items"]:
            print(f"- {item['title']} ({item['source']})")

    print("\n--- JSON completo (financial_statements) ---")
    print(json.dumps(fs, indent=2, ensure_ascii=False)[:2000])
FILE_EOF

cat > llm_provider.py << 'FILE_EOF'
"""
Camada de LLM com fallback de provedor: DeepSeek V4 Flash (thinking mode) como
primario, Groq gpt-oss-120b como fallback automatico.

Por que uma classe BaseLLM customizada em vez do wrapper padrao do CrewAI
(litellm)? Duas razoes tecnicas:

1. Ha um bug conhecido no litellm (issue #27439, maio/2026) que descarta o
   parametro reasoning_effort especificamente na integracao com DeepSeek V4,
   substituindo sempre por thinking:enabled sem controle fino.
2. O modo thinking do V4 retorna o raciocinio em `reasoning_content`,
   separado do `content` final -- controlando isso manualmente, garantimos
   que o reasoning trace NUNCA vaza pro parser de tool-calling do agente
   (o problema classico do <think> tag que quebrava o R1 antigo).

Ambos os provedores sao OpenAI-compatible, entao usamos um unico cliente
`openai.OpenAI` trocando so o base_url e a chave.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union

from crewai import BaseLLM
from openai import OpenAI

logger = logging.getLogger("llm_provider")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # thinking mode ligado via extra_body

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-120b"  # fallback gratuito permanente, tambem reasoning

MAX_TOOL_ROUNDS = 8  # trava de seguranca contra loop infinito de tool calling


class DeepSeekGroqFallbackLLM(BaseLLM):
    """LLM customizado com fallback DeepSeek -> Groq e tool-calling loop manual."""

    def __init__(
        self,
        deepseek_api_key: str,
        groq_api_key: str,
        temperature: Optional[float] = 0.3,
    ):
        # BaseLLM exige o atributo `model` -- usamos o nome do primario aqui,
        # o real provider ativo e decidido em runtime no fallback.
        super().__init__(model=DEEPSEEK_MODEL, temperature=temperature)
        self._deepseek_client = OpenAI(api_key=deepseek_api_key, base_url=DEEPSEEK_BASE_URL)
        self._groq_client = OpenAI(api_key=groq_api_key, base_url=GROQ_BASE_URL)
        self.last_provider_used: Optional[str] = None

    def supports_function_calling(self) -> bool:
        return True

    # ------------------------------------------------------------------ #
    # Interface exigida pelo BaseLLM do CrewAI
    # ------------------------------------------------------------------ #

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,  # absorve extras que versoes do CrewAI possam passar
                        # (ex: from_task, from_agent) sem quebrar a chamada
    ) -> Union[str, Any]:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        else:
            messages = list(messages)  # copia -- vamos mutar essa lista

        try:
            return self._run_tool_loop(
                client=self._deepseek_client,
                model=DEEPSEEK_MODEL,
                provider_name="deepseek",
                messages=messages,
                tools=tools,
                available_functions=available_functions,
                extra_body={"thinking": {"type": "enabled"}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "DeepSeek falhou (%s) -- caindo para Groq gpt-oss-120b", exc
            )
            return self._run_tool_loop(
                client=self._groq_client,
                model=GROQ_MODEL,
                provider_name="groq",
                messages=messages,
                tools=tools,
                available_functions=available_functions,
                extra_body=None,
            )

    # ------------------------------------------------------------------ #
    # Loop de tool calling (mantido explicito para controlar o
    # reasoning_content e nao deixar o rastro de pensamento vazar pro
    # parser de ferramentas do agente)
    # ------------------------------------------------------------------ #

    def _run_tool_loop(
        self,
        client: OpenAI,
        model: str,
        provider_name: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]],
        available_functions: Optional[Dict[str, Any]],
        extra_body: Optional[dict],
    ) -> str:
        self.last_provider_used = provider_name

        for round_num in range(MAX_TOOL_ROUNDS):
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": self.temperature,
            }
            if tools:
                kwargs["tools"] = tools
            if extra_body:
                kwargs["extra_body"] = extra_body

            response = client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            # o reasoning_content (quando existe) fica de fora do texto que
            # segue pro parser de tools -- so logamos, nunca reinjetamos no
            # content que o CrewAI vai tentar interpretar como JSON de tool.
            reasoning = getattr(message, "reasoning_content", None)
            if reasoning:
                logger.info(
                    "[%s] reasoning_content (%d chars) descartado do fluxo de tool-calling",
                    provider_name,
                    len(reasoning),
                )

            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                return message.content or ""

            if not available_functions:
                # o modelo pediu pra chamar uma tool mas nao recebemos
                # implementacoes -- devolve o texto (se houver) em vez de
                # quebrar silenciosamente.
                return message.content or ""

            # registra a resposta do assistente (com tool_calls) no historico
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}

                fn = available_functions.get(fn_name)
                if fn is None:
                    tool_result = f"erro: tool '{fn_name}' nao encontrada"
                else:
                    try:
                        tool_result = fn(**fn_args)
                    except Exception as exc:  # noqa: BLE001
                        tool_result = f"erro executando '{fn_name}': {exc}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                    }
                )

        # estourou o limite de rounds -- devolve o que tiver, nao trava o crew
        logger.error("MAX_TOOL_ROUNDS (%d) atingido para provider=%s", MAX_TOOL_ROUNDS, provider_name)
        return "Erro: numero maximo de chamadas de ferramenta excedido antes de uma resposta final."


def get_llm(deepseek_api_key: str, groq_api_key: str) -> DeepSeekGroqFallbackLLM:
    """Factory simples -- mantem agents.py desacoplado dos detalhes de provider."""
    return DeepSeekGroqFallbackLLM(
        deepseek_api_key=deepseek_api_key,
        groq_api_key=groq_api_key,
    )
FILE_EOF

cat > agents.py << 'FILE_EOF'
"""
Agentes CrewAI do pipeline de due diligence financeira.

Topologia sequencial: Data Gatherer -> Quant Analyst -> CIO.

Nota de arquitetura: a primeira versao deste arquivo usava o campo nativo
`mcps` do CrewAI (feature nova, poucos meses de existencia). Na pratica ele
disparou um RuntimeError de event loop assincrono ("no running event loop")
dentro do proprio kickoff() sincrono nessa versao do CrewAI (1.15.4) --
sintoma de uma feature ainda instavel. Trocamos para o `MCPServerAdapter`
do crewai-tools, que resolve a conexao MCP via um context manager sincrono
comum, com muito mais uso real em producao e sem essa classe de bug.
"""

from __future__ import annotations

import os
import sys

from crewai import Agent, Crew, Process, Task
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from mcp import StdioServerParameters

from llm_provider import get_llm

load_dotenv()

MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")


def _mcp_server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,  # usa o mesmo interpretador Python do processo atual
        args=[MCP_SERVER_PATH],
        env={**os.environ},
    )


def _build_crew(ticker: str, mcp_tools) -> Crew:
    deepseek_key = os.environ["DEEPSEEK_API_KEY"]
    groq_key = os.environ["GROQ_API_KEY"]
    llm = get_llm(deepseek_api_key=deepseek_key, groq_api_key=groq_key)

    data_gatherer = Agent(
        role="Data Gatherer",
        goal=(
            f"Coletar todos os dados financeiros disponiveis para o ticker {ticker}: "
            "DRE, Balanco, Fluxo de Caixa, cotacao atual e as noticias mais recentes."
        ),
        backstory=(
            "Voce e um analista de dados metodico. Sua unica responsabilidade e "
            "extrair dados brutos via as ferramentas MCP disponiveis e organiza-los "
            "claramente para o proximo agente. Voce NUNCA interpreta ou opina sobre "
            "os dados -- apenas coleta e reporta, incluindo explicitamente quando "
            "algum dado nao estiver disponivel (fundamentals_available=false)."
        ),
        tools=mcp_tools,
        llm=llm,
        verbose=True,
    )

    quant_analyst = Agent(
        role="Quant Analyst",
        goal=(
            "Calcular metricas fundamentalistas (P/L, ROE, Margem Liquida) e uma "
            "projecao de DCF simplificada a partir dos dados coletados."
        ),
        backstory=(
            "Voce e um analista quantitativo rigoroso. Trabalha exclusivamente com "
            "os dados que o Data Gatherer forneceu -- nunca inventa numeros que nao "
            "estao la. Ao apresentar o DCF, voce SEMPRE deixa explicito que e um "
            "modelo didatico simplificado (WACC fixo, sem analise de sensibilidade), "
            "nao uma ferramenta de precificacao real. Se fundamentals_available for "
            "false, voce reporta que a analise quantitativa nao pode ser realizada "
            "por falta de dados, em vez de estimar valores."
        ),
        llm=llm,
        verbose=True,
    )

    cio = Agent(
        role="CIO (Chief Investment Officer)",
        goal=(
            "Sintetizar a analise quantitativa com o sentimento das noticias recentes "
            "e produzir um relatorio final em Markdown com recomendacao de "
            "Compra/Venda/Manutencao."
        ),
        backstory=(
            "Voce e um CIO experiente e cauteloso. Seu relatorio final SEMPRE inclui "
            "um disclaimer de que esta analise e um projeto de portfolio/demonstracao "
            "tecnica, nao uma recomendacao de investimento real, e que o DCF usado e "
            "simplificado. Voce e direto: recomendacao clara, mas sempre ancorada nos "
            "dados apresentados, nunca em suposicoes."
        ),
        llm=llm,
        verbose=True,
    )

    gather_task = Task(
        description=(
            f"Use as ferramentas MCP disponiveis para coletar DRE, Balanco, Fluxo de "
            f"Caixa, cotacao atual e noticias recentes do ticker {ticker}. Reporte os "
            "dados brutos organizados, sem interpretacao."
        ),
        expected_output=(
            "Um resumo estruturado com os dados financeiros e as noticias coletadas, "
            "incluindo o status de fundamentals_available."
        ),
        agent=data_gatherer,
    )

    quant_task = Task(
        description=(
            "Com base nos dados coletados, calcule P/L, ROE, Margem Liquida e uma "
            "projecao de DCF simplificada. Se os dados fundamentais nao estiverem "
            "disponiveis, reporte isso claramente em vez de estimar."
        ),
        expected_output=(
            "Metricas calculadas com os valores usados em cada formula, e a "
            "projecao de DCF com o disclaimer de que e um modelo didatico."
        ),
        agent=quant_analyst,
        context=[gather_task],
    )

    cio_task = Task(
        description=(
            f"Produza o relatorio final em Markdown para {ticker}, combinando a "
            "analise quantitativa com o sentimento das noticias recentes. Inclua "
            "recomendacao de Compra/Venda/Manutencao e os disclaimers necessarios."
        ),
        expected_output=(
            "Relatorio em Markdown com: resumo executivo, metricas principais, "
            "sentimento de mercado, recomendacao final e disclaimers."
        ),
        agent=cio,
        context=[gather_task, quant_task],
    )

    return Crew(
        agents=[data_gatherer, quant_analyst, cio],
        tasks=[gather_task, quant_task, cio_task],
        process=Process.sequential,
        verbose=True,
    )


def run_analysis(ticker: str) -> str:
    """Ponto de entrada principal: abre a conexao MCP, monta o crew e executa.

    A conexao MCP (subprocesso stdio) precisa ficar viva durante toda a
    execucao do crew -- por isso o kickoff() acontece dentro do `with`.
    """
    server_params = _mcp_server_params()
    with MCPServerAdapter(server_params) as mcp_tools:
        print(f"Tools MCP carregadas: {[t.name for t in mcp_tools]}")
        crew = _build_crew(ticker, mcp_tools)
        result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    final_report = run_analysis(ticker_arg)
    print("\n\n=== RELATORIO FINAL ===\n")
    print(final_report)

FILE_EOF

echo "6 arquivos criados/atualizados com sucesso."