"""Yahoo Finance financial adapter and MCP news tools for the B3 contract."""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Literal, Optional

import yfinance as yf
from ddgs import DDGS
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, FiniteFloat, model_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from financial_data import load_snapshot, timestamp, currency_code
from news_data import news_date, news_url, order_news
from yahoo_statements import fetch_statement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("financial-analyst-tools")


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class Quote(BaseModel):
    price: FiniteFloat = Field(gt=0)
    currency: Optional[str] = None
    symbol: Optional[str] = None
    source: str = "yfinance"
    as_of: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinancialStatements(BaseModel):
    ticker: str
    provider_used: str = "yfinance"
    quote: Optional[Quote] = None
    income_statement: dict[str, dict[str, FiniteFloat | None]] = Field(default_factory=dict)
    balance_sheet: dict[str, dict[str, FiniteFloat | None]] = Field(default_factory=dict)
    cash_flow: dict[str, dict[str, FiniteFloat | None]] = Field(default_factory=dict)
    fundamentals_available: bool = Field(
        default=False,
        description="True quando os tres demonstrativos contem valores numericos validos. "
        "Nao garante os campos, periodos ou denominadores necessarios a cada metrica."
    )
    warning: Optional[str] = None
    statement_metadata: dict[str, dict[str, dict]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_availability(self):
        # Availability means all three statements contain numeric data;
        # it does not guarantee that every metric can be calculated.
        missing = [
            name for name in ("income_statement", "balance_sheet", "cash_flow")
            if not any(value is not None for period in getattr(self, name).values()
                       for value in period.values())
        ]
        self.fundamentals_available = not missing
        warnings = [self.warning] if self.warning else []
        if missing:
            warnings.append("Demonstrativos ausentes ou sem valores validos: " + ", ".join(missing) + ".")
        if self.quote is None:
            warnings.append("Cotacao ausente ou invalida; nao calcular metricas que dependem do preco.")
        self.warning = " ".join(warnings) or None
        return self


class NewsItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    date_raw: str | None = None
    published_at: str | None = None
    date_status: Literal["missing", "invalid", "timezone_missing", "future", "reported"] = "missing"
    date_label: str
    date_origin: str = "ddgs.news.date"
    article_verified: bool = False


class MarketNews(BaseModel):
    ticker: str
    query: str
    retrieved_at: datetime
    provider: str = "ddgs"
    items: list[NewsItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


MAX_PERIODS = 2  # so os 2 periodos mais recentes -- o JSON com 5 anos e ~30
                 # linhas por demonstrativo ficava grande demais e estourava
                 # o orcamento de contexto do free tier do Groq apos a tool
                 # ser chamada (historico da conversa cresce com o resultado)

# linhas que realmente importam pro Quant Analyst calcular P/L, ROE, Margem
# Liquida e DCF -- o restante e ruido que so consome tokens sem agregar.
_ESSENTIAL_INCOME_STATEMENT = {
    "Total Operating Income As Reported",
    "Total Revenue", "Gross Profit", "Operating Income", "EBITDA", "EBIT",
    "Net Income", "Total Expenses", "Diluted EPS", "Basic EPS", "Pretax Income",
}
_ESSENTIAL_BALANCE_SHEET = {
    "Total Assets", "Total Liabilities Net Minority Interest",
    "Total Equity Gross Minority Interest", "Total Debt", "Cash And Cash Equivalents",
    "Common Stock Equity",
    "Stockholders Equity",
}
_ESSENTIAL_CASH_FLOW = {
    "Free Cash Flow", "Operating Cash Flow", "Capital Expenditure",
    "Net Income From Continuing Operations",
}


def _finite_number(value) -> float | None:
    """Preserve zero/negative accounting values, never fabricate missing data."""
    if value is None or isinstance(value, (bool, str, bytes)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _df_to_nested_dict(
    df, essential_rows: Optional[set[str]] = None
) -> dict[str, dict[str, float | None]]:
    """Converte um DataFrame do yfinance (linhas=conta, colunas=periodo) em
    dict serializavel: {periodo_iso: {conta: valor}}.

    Limita a MAX_PERIODS colunas mais recentes e, se essential_rows for
    passado, filtra so as linhas relevantes -- mantem o payload pequeno o
    suficiente pra nao estourar o orcamento de contexto dos providers
    gratuitos depois que a tool roda.
    """
    if df is None or df.empty:
        return {}
    out: dict[str, dict[str, float | None]] = {}
    for col in sorted(df.columns, reverse=True)[:MAX_PERIODS]:
        period_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        rows = {
            str(idx): _finite_number(val)
            for idx, val in df[col].items()
            if essential_rows is None or str(idx) in essential_rows
        }
        out[period_key] = rows
    return out


def _get_financial_statements_yfinance(ticker: str) -> dict:
    try:
        t = _fetch_yfinance(ticker)
        try:
            info = t.get_info()
            if not isinstance(info, dict):
                info = {}
        except Exception:
            info = {}
        # Recent yfinance versions retire quote fields from get_info(). Fetch
        # chart metadata as one observation; never pair its time with fast_info.
        quote_info = info
        if (info.get("symbol") != ticker or not currency_code(info.get("currency"))
                or not timestamp(info.get("regularMarketTime"))
                or (_finite_number(info.get("regularMarketPrice")) or 0) <= 0):
            try:
                chart = t.get_history_metadata()
                if (isinstance(chart, Mapping) and chart.get("symbol") == ticker
                        and currency_code(chart.get("currency"))
                        and (_finite_number(chart.get("regularMarketPrice")) or 0) > 0):
                    quote_info = chart
            except Exception:
                pass  # Existing partial-data handling remains available.
        # fast_info nao e um dict comum -- acesso por atributo e o caminho
        # confiavel entre versoes do yfinance. .get("last_price") sempre
        # cai no default e mascara o preco real como 0.0 silenciosamente.
        try:
            raw_price = _finite_number(quote_info.get("regularMarketPrice"))
            quote_time = timestamp(quote_info.get("regularMarketTime"))
            if raw_price is None:
                raw_price = _finite_number(getattr(t.fast_info, "last_price", None))
                quote_time = None  # fast_info has no timestamp paired with last_price.
            raw_currency = quote_info.get("currency") or getattr(t.fast_info, "currency", None)
            quote = Quote(
                price=raw_price,
                currency=currency_code(raw_currency),
                symbol=quote_info.get("symbol"),
                source="yfinance",
                as_of=quote_time,
            )
        except Exception:
            quote = None

        statements = {}
        metadata = {}
        warnings = []
        for name, attribute, rows in (
            ("income_statement", "financials", _ESSENTIAL_INCOME_STATEMENT),
            ("balance_sheet", "balance_sheet", _ESSENTIAL_BALANCE_SHEET),
            ("cash_flow", "cashflow", _ESSENTIAL_CASH_FLOW),
        ):
            try:
                statements[name], metadata[name] = fetch_statement(t, ticker, rows)
            except Exception:
                statements[name] = {}
                warnings.append(f"Falha ao obter {name} via yfinance.")

        result = FinancialStatements(
            ticker=ticker,
            provider_used="yfinance",
            quote=quote,
            **statements,
            statement_metadata=metadata,
            fundamentals_available=True,
            warning=" ".join(warnings) or None,
        )
        return result.model_dump(mode="json")

    except Exception as exc:  # noqa: BLE001
        logger.error("yfinance indisponivel para %s (%s)", ticker, type(exc).__name__)
        result = FinancialStatements(
            ticker=ticker, provider_used="yfinance", fundamentals_available=False,
            warning="Yahoo Finance indisponivel. Tente novamente mais tarde.",
        )
        return result.model_dump(mode="json")


@mcp.tool()
def get_financial_statements(ticker: str, market: str = "BR") -> dict:
    """Contrato B3 v3: dados Yahoo Finance validados, periodos, moedas e origem.

    Aceita PETR4 ou PETR4.SA. Sem selecao de fonte; falhas produzem dados
    parciais ou indisponiveis com avisos, sem consultar outros provedores.
    """
    return load_snapshot(ticker, _get_financial_statements_yfinance, market=market)


@mcp.tool()
def get_market_news(ticker: str, max_results: int = 3) -> dict:
    """Busca notícias via ddgs com URLs e datas rastreáveis, não verificadas no artigo.

    Use date_label no relatório. retrieved_at é consulta, não publicação. Datas
    futuras, inválidas ou sem fuso não são aceitas como publicação confirmada.
    """
    # tickers brasileiros (.SA) tem pouco resultado com query em ingles
    # generica -- adicionar "acoes" ajuda o ddgs a achar cobertura local
    query = f"{ticker} acoes" if ticker.upper().endswith(".SA") else f"{ticker} stock"
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.news(query, max_results=max_results))
        retrieved_at = datetime.now(timezone.utc)
        items = []
        warnings = []
        for r in raw:
            url = news_url(r.get("url")) if isinstance(r, dict) else None
            if not url:
                warnings.append("Resultado descartado: link HTTP(S) ausente ou inválido.")
                continue
            title = r.get("title")
            if not isinstance(title, str) or not title.strip():
                warnings.append("Resultado descartado: título ausente ou inválido.")
                continue
            items.append(NewsItem(
                title=title, url=url,
                snippet=r["body"][:200] if isinstance(r.get("body"), str) else "",
                source=r["source"] if isinstance(r.get("source"), str) else "",
                **news_date(r.get("date"), retrieved_at),
            ))
        return MarketNews(ticker=ticker, query=query, retrieved_at=retrieved_at,
                          items=order_news(items, retrieved_at),
                          warnings=list(dict.fromkeys(warnings))).model_dump(mode="json")

    except Exception as exc:  # noqa: BLE001
        logger.error("ddgs falhou para %s (%s)", ticker, type(exc).__name__)
        return ToolError(error="Não foi possível consultar as notícias. Datas e fontes não confirmadas.",
                         ticker=ticker).model_dump(mode="json")


if __name__ == "__main__":
    mcp.run(transport="stdio")
