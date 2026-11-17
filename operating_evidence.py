"""Opt-in diagnostic collection, deliberately outside the app/LLM data contract."""
from datetime import datetime, timezone

from financial_data import normalize_ticker
from yahoo_statements import fetch_statement

REPORTED_FIELD = "Total Operating Income As Reported"


def collect_reported_operating_income(client, ticker, *, now=None):
    ticker = normalize_ticker(ticker)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Collection timestamp must include a timezone")
    values, metadata = fetch_statement(client, ticker, {REPORTED_FIELD})
    observations = []
    for end, row in sorted(values.items(), reverse=True):
        meta = metadata[end]
        if end > now.date().isoformat():
            continue
        # Unknown/conflicting currency must not become a usable observation.
        if not meta["currency"]:
            continue
        observations.append({
            "period_end": end, "period_type": "annual",
            "currency": meta["currency"], "unit": "currency_units",
            "value": row[REPORTED_FIELD],
        })
    return {
        "ticker": ticker, "retrieved_at": now.isoformat(),
        "source": "Yahoo fundamentals-timeseries",
        "source_field": "annualTotalOperatingIncomeAsReported",
        "validation_status": "unverified", "eligible_for_analysis": False,
        "observations": observations,
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    import yfinance as yf

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", choices=["PETR4", "VALE3"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", required=True)
    args = parser.parse_args()
    yf.set_tz_cache_location(args.cache_dir)
    evidence = collect_reported_operating_income(yf.Ticker(normalize_ticker(args.ticker)), args.ticker)
    # Never replace previous evidence silently.
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(evidence, output, ensure_ascii=False, indent=2)
