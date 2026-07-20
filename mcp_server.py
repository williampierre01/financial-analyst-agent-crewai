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


MAX_PERIODS = 2  # so os 2 periodos mais recentes -- o JSON com 5 anos e ~30
                 # linhas por demonstrativo ficava grande demais e estourava
                 # o orcamento de contexto do free tier do Groq apos a tool
                 # ser chamada (historico da conversa cresce com o resultado)

# linhas que realmente importam pro Quant Analyst calcular P/L, ROE, Margem
# Liquida e DCF -- o restante e ruido que so consome tokens sem agregar.
_ESSENTIAL_INCOME_STATEMENT = {
    "Total Revenue", "Gross Profit", "Operating Income", "EBITDA", "EBIT",
    "Net Income", "Total Expenses", "Diluted EPS", "Basic EPS", "Pretax Income",
}
_ESSENTIAL_BALANCE_SHEET = {
    "Total Assets", "Total Liabilities Net Minority Interest",
    "Total Equity Gross Minority Interest", "Total Debt", "Cash And Cash Equivalents",
    "Common Stock Equity",
}
_ESSENTIAL_CASH_FLOW = {
    "Free Cash Flow", "Operating Cash Flow", "Capital Expenditure",
    "Net Income From Continuing Operations",
}


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
    for col in df.columns[:MAX_PERIODS]:
        period_key = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        rows = {
            str(idx): (float(val) if val == val else None)  # val==val descarta NaN
            for idx, val in df[col].items()
            if essential_rows is None or str(idx) in essential_rows
        }
        out[period_key] = rows
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
            income_statement=_df_to_nested_dict(t.financials, _ESSENTIAL_INCOME_STATEMENT),
            balance_sheet=_df_to_nested_dict(t.balance_sheet, _ESSENTIAL_BALANCE_SHEET),
            cash_flow=_df_to_nested_dict(t.cashflow, _ESSENTIAL_CASH_FLOW),
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
def get_market_news(ticker: str, max_results: int = 3) -> dict:
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
                snippet=(r.get("body", "") or "")[:200],
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