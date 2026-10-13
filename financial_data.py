"""Validated Yahoo Finance data contract for B3.

Native Yahoo fields are mapped at this boundary.
No cross-currency or cross-period merging is performed.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta, timezone
from typing import Callable


FIELDS = {
    "income_statement": {
        "revenue": ("Receita", "Total Revenue"),
        "net_income": ("Lucro líquido", "Net Income"),
        "operating_income": ("Resultado operacional", "Operating Income"),
        "diluted_eps": ("Lucro diluído por ação", "Diluted EPS"),
    },
    "balance_sheet": {
        "total_assets": ("Ativo total", "Total Assets"),
        "stockholders_equity": ("Patrimônio dos acionistas", "Stockholders Equity"),
        "total_debt": ("Dívida total", "Total Debt"),
        "cash": ("Caixa e equivalentes", "Cash And Cash Equivalents"),
    },
    "cash_flow": {
        "operating_cash_flow": ("Fluxo de caixa operacional", "Operating Cash Flow"),
        "free_cash_flow": ("Fluxo de caixa livre", "Free Cash Flow"),
    },
}
REQUIRED = {
    "income_statement": ("revenue", "net_income"),
    "balance_sheet": ("stockholders_equity",),
    "cash_flow": ("operating_cash_flow", "free_cash_flow"),
}
SOURCE = "yfinance"
# Calendar-day policies, not a trading-session calendar or a realtime guarantee.
QUOTE_MAX_AGE = timedelta(days=7)
STATEMENT_MAX_AGE = timedelta(days=550)


def normalize_ticker(ticker: str, market: str = "BR") -> str:
    if market != "BR":
        raise ValueError("Mercado ainda não suportado. Use ações brasileiras (B3).")
    symbol = (ticker or "").strip().upper()
    if symbol.endswith(".SA"):
        symbol = symbol[:-3]
    if not re.fullmatch(r"[A-Z]{4}[0-9]{1,2}", symbol):
        raise ValueError("Informe um código da B3, como PETR4, VALE3 ou ITUB4.")
    return symbol + ".SA"


def finite_number(value):
    if isinstance(value, (bool, str, bytes)) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError, OverflowError):
        return None


def currency_code(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Z]{3}", value) else None


def timestamp(value):
    try:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def normalize_snapshot(raw: dict, ticker: str, now: datetime) -> dict:
    warnings = []
    statements = {}
    metadata = raw.get("statement_metadata", {})
    for group, fields in FIELDS.items():
        periods = []
        for end, values in raw.get(group, {}).items():
            try:
                end_date = date.fromisoformat(end)
                if end_date > now.date():
                    raise ValueError("future period")
            except (ValueError, TypeError):
                warnings.append(f"Período inválido descartado em {group}.")
                continue
            meta = metadata.get(group, {}).get(end, {})
            if meta.get("symbol") != ticker or meta.get("period") != "FY":
                warnings.append(f"{group}: identidade ou período anual não confirmado; dados descartados.")
                continue
            currency = currency_code(meta.get("currency"))
            mapped = {key: finite_number(values.get(names[1])) for key, names in fields.items()}
            missing = [key for key in REQUIRED[group] if mapped[key] is None]
            periods.append({
                "period_end": end_date.isoformat(), "period_type": "annual", "currency": currency,
                "source": SOURCE, "unit": "currency_units", "per_share_fields": ["diluted_eps"] if group == "income_statement" else [],
                "values": mapped, "missing_fields": missing,
            })
            if not currency:
                warnings.append(f"Moeda dos demonstrativos não informada em {group} ({end}).")
        statements[group] = sorted(periods, key=lambda p: p["period_end"], reverse=True)[:2]

    quote = None
    q = raw.get("quote") or {}
    price = finite_number(q.get("price"))
    if (price is not None and price > 0 and q.get("currency") == "BRL"
            and q.get("source") == SOURCE and q.get("symbol") == ticker):
        as_of = timestamp(q.get("as_of"))
        if as_of and as_of > now + timedelta(minutes=5):
            as_of = None
            warnings.append("Data futura da cotação descartada.")
        quote = {"price": price, "currency": "BRL", "source": SOURCE,
                 "as_of": as_of.isoformat() if as_of else None,
                 "freshness": "unknown" if as_of is None else "stale" if now - as_of > QUOTE_MAX_AGE else "recent"}
        if quote["freshness"] != "recent":
            warnings.append("Cotação sem data confirmada ou com mais de 7 dias; não tratá-la como preço atual.")
    else:
        warnings.append("Cotação em BRL indisponível ou inválida; nenhum câmbio foi presumido.")

    # Require the same annual period and known currency for all three statements.
    candidates = set.intersection(*[
        {p["period_end"] for p in periods if not p["missing_fields"] and p["currency"]}
        for periods in statements.values()
    ])
    aligned = []
    for end in candidates:
        rows = [next(p for p in periods if p["period_end"] == end) for periods in statements.values()]
        if len({p["currency"] for p in rows}) == 1:
            aligned.append(end)
    common_period = max(aligned, default=None)
    fundamentals_available = common_period is not None
    recent_fundamentals = bool(common_period and now.date() - date.fromisoformat(common_period) <= STATEMENT_MAX_AGE)
    if not fundamentals_available:
        warnings.append("Base anual incompleta: faltam campos essenciais, moeda confirmada ou período comum aos demonstrativos.")
    elif not recent_fundamentals:
        warnings.append("Último período anual completo tem mais de 550 dias.")
    if any(p["missing_fields"] for periods in statements.values() for p in periods):
        warnings.append("Há campos essenciais ausentes; consulte os campos indisponíveis na tabela.")
    financial_currency = next((p["currency"] for p in statements["income_statement"] if p["period_end"] == common_period), None)
    if quote and financial_currency and financial_currency != quote["currency"]:
        warnings.append("Moeda dos demonstrativos difere da cotação; não combinar valores sem conversão validada.")
    has_values = any(v is not None for periods in statements.values() for p in periods for v in p["values"].values())
    complete = bool(recent_fundamentals and quote and quote["freshness"] == "recent" and financial_currency == "BRL")
    return {
        "schema_version": "3.0", "ticker": ticker, "display_ticker": ticker.removesuffix(".SA"),
        "market": "BR", "exchange": "B3", "provider_used": SOURCE,
        "retrieved_at": now.isoformat(), "quote": quote, "statements": statements,
        "fundamentals_available": fundamentals_available, "common_period": common_period,
        "status": "complete" if complete else "partial" if has_values or quote else "unavailable",
        "warnings": list(dict.fromkeys(warnings)),
    }


def load_snapshot(ticker: str, loader: Callable, *, market: str = "BR",
                  now: datetime | None = None) -> dict:
    """Load Yahoo once and return explicit partial/unavailable states on failure."""
    ticker = normalize_ticker(ticker, market)
    now = now or datetime.now(timezone.utc)
    try:
        snapshot = normalize_snapshot(loader(ticker), ticker, now)
    except Exception:
        snapshot = normalize_snapshot({}, ticker, now)
        snapshot["warnings"].append("Não foi possível consultar o Yahoo Finance. Tente novamente mais tarde.")
    if snapshot["status"] == "unavailable":
        snapshot["provider_used"] = None
    return snapshot


def render_data_report(snapshot: dict) -> str:
    """Fixed, localised client table; numbers and provenance never come from an LLM."""
    def number(value):
        if value is None:
            return "Não disponível"
        return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    labels = {"complete": "Base disponível", "partial": "Dados parciais", "unavailable": "Dados indisponíveis"}
    source = "Yahoo Finance" if snapshot["provider_used"] == SOURCE else "Yahoo Finance (dados indisponíveis)"
    quote = snapshot["quote"]
    lines = [f"## Dados de {snapshot['display_ticker']} · B3", f"**Situação:** {labels[snapshot['status']]} · **Fonte:** {source}",
             f"**Consultado em (UTC):** {snapshot['retrieved_at']}",
             f"**Cotação:** {'R$ ' + number(quote['price']) if quote else 'Não disponível'}",
             f"**Data da cotação (UTC):** {quote['as_of'] if quote and quote['as_of'] else 'Não informada pela fonte'}",
             "", "Valores em unidades da moeda indicada; lucro por ação em moeda por ação. Sem conversão cambial.",
             "", "| Informação | Período anual encerrado em | Moeda | Valor |", "|---|---|---|---:|"]
    for group, fields in FIELDS.items():
        periods = snapshot["statements"][group] or [{"period_end": "Não disponível", "currency": None, "values": {}}]
        for period in periods:
            for key, names in fields.items():
                lines.append(f"| {names[0]} | {period['period_end']} | {period['currency'] or 'Não informada'} | {number(period['values'].get(key))} |")
    if snapshot["warnings"]:
        lines += ["", "**Limitações dos dados**", ""] + [f"- {w}" for w in snapshot["warnings"]]
    lines += ["", "Demonstração técnica; não constitui recomendação de investimento."]
    return "\n".join(lines)
