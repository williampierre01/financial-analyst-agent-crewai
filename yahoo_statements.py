"""Preserve currency attached to Yahoo timeseries values, before tabular flattening."""

import math
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

from financial_data import currency_code


def parse_statement(payload, ticker, rows):
    values, currencies = {}, {}
    series = (payload.get("timeseries") or {}).get("result") or []
    for entry in series:
        if entry.get("meta", {}).get("symbol") != [ticker]:
            continue
        for label in rows:
            key = "annual" + label.replace(" ", "")
            for point in entry.get(key, []):
                end = point.get("asOfDate")
                try:
                    date.fromisoformat(end)
                except (ValueError, TypeError):
                    continue
                if point.get("periodType") != "12M":
                    continue
                raw = (point.get("reportedValue") or {}).get("raw")
                if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw):
                    continue
                # Conflicting duplicates must not silently overwrite an observation.
                previous = values.setdefault(end, {}).get(label)
                if previous is not None and previous != raw:
                    raise ValueError("Conflicting Yahoo observations")
                values[end][label] = raw
                currencies.setdefault(end, set()).add(currency_code(point.get("currencyCode")))
    ends = sorted(values, reverse=True)[:2]
    metadata = {
        end: {"symbol": ticker, "period": "FY",
              "currency": next(iter(currencies[end])) if len(currencies[end]) == 1 else None}
        for end in ends
    }
    return {end: values[end] for end in ends}, metadata


def fetch_statement(client, ticker, rows):
    # yfinance's DataFrame discards currencyCode. Use its authenticated transport
    # against the same timeseries endpoint, retaining per-observation metadata.
    params = urlencode({
        "symbol": ticker,
        "type": ",".join("annual" + label.replace(" ", "") for label in sorted(rows)),
        "period1": int(datetime(2016, 12, 31, tzinfo=timezone.utc).timestamp()),
        "period2": int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    })
    url = f"https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{ticker}?{params}"
    payload = client._data.cache_get(url=url).json()
    return parse_statement(payload, ticker, rows)
