import unittest
from collections import UserDict
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

import mcp_server as server
from financial_data import normalize_snapshot
from test_yahoo_contract import NOW, SYMBOL


class AdapterTests(unittest.TestCase):
    def test_yahoo_preserves_financial_currency_and_quote_time(self):
        info = {"symbol": SYMBOL, "currency": "BRL", "financialCurrency": "BRL",
                "regularMarketPrice": 30, "regularMarketTime": int(NOW.timestamp())}
        obj = SimpleNamespace(
            get_info=lambda: info,
            financials=pd.DataFrame({pd.Timestamp("2025-12-31"): {"Total Revenue": 100, "Net Income": 10}}),
            balance_sheet=pd.DataFrame({pd.Timestamp("2025-12-31"): {"Stockholders Equity": 50}}),
            cashflow=pd.DataFrame({pd.Timestamp("2025-12-31"): {"Operating Cash Flow": 20, "Free Cash Flow": 15}}),
        )
        def statements(client, symbol, rows):
            attribute = ("financials" if rows == server._ESSENTIAL_INCOME_STATEMENT else
                         "balance_sheet" if rows == server._ESSENTIAL_BALANCE_SHEET else "cashflow")
            values = server._df_to_nested_dict(getattr(client, attribute), rows)
            return values, {end: {"currency": "BRL", "symbol": symbol, "period": "FY"} for end in values}
        with patch.object(server, "_fetch_yfinance", return_value=obj), \
                patch.object(server, "fetch_statement", side_effect=statements):
            raw = server._get_financial_statements_yfinance(SYMBOL)
        result = normalize_snapshot(raw, SYMBOL, NOW)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["quote"]["as_of"], NOW.isoformat())
        self.assertEqual(result["statements"]["income_statement"][0]["currency"], "BRL")

    def test_yahoo_fast_quote_has_no_invented_timestamp(self):
        obj = SimpleNamespace(get_info=lambda: {"symbol": SYMBOL},
                              fast_info=SimpleNamespace(last_price=20, currency="BRL"),
                              financials=None, balance_sheet=None, cashflow=None)
        with patch.object(server, "_fetch_yfinance", return_value=obj):
            raw = server._get_financial_statements_yfinance(SYMBOL)
        self.assertIsNone(raw["quote"]["as_of"])
        result = normalize_snapshot(raw, SYMBOL, NOW)
        self.assertEqual(result["quote"]["freshness"], "unknown")

    def test_retired_info_fields_use_chart_observation(self):
        for symbol in ("PETR4.SA", "VALE3.SA"):
            obj = SimpleNamespace(
                get_info=lambda: {"financialCurrency": "USD"},
                get_history_metadata=lambda: UserDict({"symbol": symbol, "currency": "BRL",
                    "regularMarketPrice": 57.75, "regularMarketTime": int(NOW.timestamp())}),
                fast_info=SimpleNamespace(last_price=999, currency="USD"),
            )
            with patch.object(server, "_fetch_yfinance", return_value=obj), \
                    patch.object(server, "fetch_statement", return_value=({}, {})):
                raw = server._get_financial_statements_yfinance(symbol)
            result = normalize_snapshot(raw, symbol, NOW)
            self.assertEqual(result["quote"]["price"], 57.75)
            self.assertEqual(result["quote"]["currency"], "BRL")
            self.assertEqual(result["quote"]["as_of"], NOW.isoformat())
            self.assertEqual(result["quote"]["freshness"], "recent")

    def test_chart_symbol_mismatch_is_not_relabelled(self):
        obj = SimpleNamespace(get_info=lambda: {}, get_history_metadata=lambda: {
            "symbol": "VALE3.SA", "currency": "BRL", "regularMarketPrice": 50,
            "regularMarketTime": int(NOW.timestamp())})
        with patch.object(server, "_fetch_yfinance", return_value=obj), \
                patch.object(server, "fetch_statement", return_value=({}, {})):
            result = server._get_financial_statements_yfinance(SYMBOL)
        self.assertIsNone(result["quote"])

    def test_chart_without_time_does_not_borrow_time_from_info(self):
        obj = SimpleNamespace(get_info=lambda: {"regularMarketTime": int(NOW.timestamp())},
            get_history_metadata=lambda: {"symbol": SYMBOL, "currency": "BRL",
                                          "regularMarketPrice": 50})
        with patch.object(server, "_fetch_yfinance", return_value=obj), \
                patch.object(server, "fetch_statement", return_value=({}, {})):
            raw = server._get_financial_statements_yfinance(SYMBOL)
        self.assertIsNone(raw["quote"]["as_of"])
        self.assertEqual(normalize_snapshot(raw, SYMBOL, NOW)["quote"]["freshness"], "unknown")


if __name__ == "__main__":
    unittest.main()
