import unittest
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
        with patch.object(server, "_fetch_yfinance", return_value=obj):
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


if __name__ == "__main__":
    unittest.main()
