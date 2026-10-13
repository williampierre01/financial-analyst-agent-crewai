"""Regression tests with simulated providers; no credentials or network needed."""
import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch, Mock

import pandas as pd
from pydantic import ValidationError

import mcp_server as server


def frame(name, value=10):
    return pd.DataFrame({pd.Timestamp("2025-12-31"): {name: value}})


def ticker(price=100):
    return SimpleNamespace(
        fast_info=SimpleNamespace(last_price=price, currency="USD"),
        financials=frame("Net Income"),
        balance_sheet=frame("Common Stock Equity"),
        cashflow=frame("Free Cash Flow"),
    )


class DataValidationTests(unittest.TestCase):
    def yahoo(self, obj):
        with patch.object(server, "_fetch_yfinance", return_value=obj):
            result = server._get_financial_statements_yfinance("AAPL")
            json.dumps(result, allow_nan=False)
            return result

    def test_valid_statements_and_quote(self):
        result = self.yahoo(ticker())
        self.assertTrue(result["fundamentals_available"])
        self.assertEqual(result["quote"]["price"], 100)
        self.assertIsNone(result["warning"])

    def test_missing_or_invalid_price_preserves_fundamentals(self):
        for price in (None, 0, -1, float("nan"), float("inf"), True):
            with self.subTest(price=price):
                result = self.yahoo(ticker(price))
                self.assertIsNone(result["quote"])
                self.assertTrue(result["fundamentals_available"])
                self.assertIn("Cotacao", result["warning"])


    def test_empty_statements_are_unavailable(self):
        obj = ticker()
        obj.financials = obj.balance_sheet = obj.cashflow = pd.DataFrame()
        result = self.yahoo(obj)
        self.assertFalse(result["fundamentals_available"])
        self.assertIsNotNone(result["quote"])

    def test_partial_data_is_preserved(self):
        obj = ticker()
        obj.balance_sheet = pd.DataFrame()
        result = self.yahoo(obj)
        self.assertFalse(result["fundamentals_available"])
        self.assertTrue(result["income_statement"])
        self.assertTrue(result["cash_flow"])
        self.assertIn("balance_sheet", result["warning"])

    def test_statement_fetch_failure_preserves_other_data(self):
        class BrokenBalance:
            fast_info = ticker().fast_info
            financials = ticker().financials
            cashflow = ticker().cashflow

            @property
            def balance_sheet(self):
                raise RuntimeError("upstream unavailable")

        result = self.yahoo(BrokenBalance())
        self.assertFalse(result["fundamentals_available"])
        self.assertTrue(result["income_statement"])
        self.assertIsNotNone(result["quote"])

    def test_nonfinite_and_missing_values_become_null(self):
        for value in (None, pd.NA, float("nan"), float("inf"), -float("inf"), True, "bad"):
            with self.subTest(value=value):
                obj = ticker()
                obj.financials = frame("Net Income", value)
                result = self.yahoo(obj)
                self.assertIsNone(result["income_statement"]["2025-12-31"]["Net Income"])
                self.assertFalse(result["fundamentals_available"])

    def test_zero_and_negative_accounting_values_are_valid(self):
        for value in (0, -10):
            obj = ticker()
            obj.financials = frame("Net Income", value)
            result = self.yahoo(obj)
            self.assertTrue(result["fundamentals_available"])
            self.assertEqual(result["income_statement"]["2025-12-31"]["Net Income"], value)

    def test_quote_schema_rejects_invalid_prices(self):
        for price in (0, -1, float("nan"), float("inf")):
            with self.subTest(price=price), self.assertRaises(ValidationError):
                server.Quote(price=price, source="yfinance", as_of=datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()
