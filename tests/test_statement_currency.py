import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import mcp_server as server
from yahoo_statements import parse_statement, fetch_statement
from financial_data import normalize_snapshot
from verified_metrics import calculate_metrics
from test_yahoo_contract import NOW, SYMBOL


def payload(currency="USD", symbol=SYMBOL, period="12M"):
    rows = {"TotalRevenue": 89_195_000_000, "NetIncome": 19_634_000_000,
            "DilutedEPS": 1.52, "StockholdersEquity": 75_565_000_000,
            "OperatingCashFlow": 36_047_000_000, "FreeCashFlow": 16_526_000_000}
    return {"timeseries": {"result": [
        {"meta": {"symbol": [symbol], "type": ["annual" + key]},
         "annual" + key: [{"asOfDate": "2025-12-31", "periodType": period,
                           "currencyCode": currency, "reportedValue": {"raw": value}}]}
        for key, value in rows.items()
    ]}}


class StatementCurrencyTests(unittest.TestCase):
    def test_raw_currency_overrides_general_company_currency_and_blocks_pe(self):
        client = SimpleNamespace(
            get_info=lambda: {"symbol": SYMBOL, "currency": "BRL", "financialCurrency": "BRL",
                              "regularMarketPrice": 57.75, "regularMarketTime": int(NOW.timestamp())},
            _data=Mock(),
        )
        client._data.cache_get.return_value.json.return_value = payload()
        with patch.object(server, "_fetch_yfinance", return_value=client):
            raw = server._get_financial_statements_yfinance(SYMBOL)
        snapshot = normalize_snapshot(raw, SYMBOL, NOW)
        income = snapshot["statements"]["income_statement"][0]
        self.assertEqual(income["currency"], "USD")
        self.assertEqual(income["values"]["revenue"], 89_195_000_000)
        self.assertEqual(income["values"]["diluted_eps"], 1.52)
        pe = next(m for m in calculate_metrics(snapshot) if m["name"] == "P/L")
        self.assertEqual(pe["status"], "unavailable")
        self.assertIn("Moedas", pe["reason"])

    def test_unknown_currency_is_not_inferred(self):
        values, meta = parse_statement(payload(None), SYMBOL, {"Total Revenue"})
        self.assertEqual(values["2025-12-31"]["Total Revenue"], 89_195_000_000)
        self.assertIsNone(meta["2025-12-31"]["currency"])

    def test_mixed_currencies_cannot_be_labeled_as_one(self):
        raw = payload()
        raw["timeseries"]["result"][1]["annualNetIncome"][0]["currencyCode"] = "BRL"
        _, meta = parse_statement(raw, SYMBOL, {"Total Revenue", "Net Income"})
        self.assertIsNone(meta["2025-12-31"]["currency"])

    def test_foreign_symbol_and_nonannual_observations_are_rejected(self):
        for raw in (payload(symbol="VALE3.SA"), payload(period="3M")):
            self.assertEqual(parse_statement(raw, SYMBOL, {"Total Revenue"}), ({}, {}))

    def test_transport_failure_does_not_fall_back_to_unverified_currency(self):
        client = SimpleNamespace(_data=Mock())
        client._data.cache_get.side_effect = RuntimeError("unavailable")
        with self.assertRaises(RuntimeError):
            fetch_statement(client, SYMBOL, {"Total Revenue"})
