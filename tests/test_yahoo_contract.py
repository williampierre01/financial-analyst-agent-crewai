"""Yahoo-only B3 contract and deterministic client output."""
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import financial_data as data
import mcp_server as server

NOW = datetime(2026, 10, 13, 15, tzinfo=timezone.utc)
SYMBOL = "PETR4.SA"


def payload(end="2025-12-31", currency="BRL"):
    values = {
        "income_statement": {"Total Revenue": 1000, "Net Income": -100, "Diluted EPS": 0},
        "balance_sheet": {"Stockholders Equity": 2000},
        "cash_flow": {"Operating Cash Flow": 300, "Free Cash Flow": 100},
    }
    return {
        **{group: {end: fields} for group, fields in values.items()},
        "quote": {"price": 32.51, "currency": "BRL", "symbol": SYMBOL,
                  "source": "yfinance", "as_of": "2026-10-13T13:00:00+00:00"},
        "statement_metadata": {
            group: {end: {"currency": currency, "symbol": SYMBOL, "period": "FY"}}
            for group in values
        },
    }


class YahooContractTests(unittest.TestCase):
    def load(self, raw=None):
        self.loader = Mock(return_value=payload() if raw is None else raw)
        return data.load_snapshot("petr4", self.loader, now=NOW)

    def test_brazilian_symbols(self):
        for value in ("petr4", " PETR4.SA ", "PETR4"):
            self.assertEqual(data.normalize_ticker(value), SYMBOL)
        self.assertEqual(data.normalize_ticker("TAEE11"), "TAEE11.SA")
        for value in ("", "AAPL", "PETR4.US", "PETR4.SA.SA", "PETR4;DROP", "PETR4\nextra"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                data.normalize_ticker(value)
        with self.assertRaises(ValueError):
            data.normalize_ticker("AAPL", market="US")

    def test_yahoo_data_is_normalized_once(self):
        result = self.load()
        self.assertEqual(result["provider_used"], "yfinance")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["schema_version"], "3.1")
        self.assertNotIn("selection", result)
        self.loader.assert_called_once_with(SYMBOL)
        values = result["statements"]["income_statement"][0]["values"]
        self.assertEqual(values["revenue"], 1000)
        self.assertEqual(values["net_income"], -100)
        self.assertEqual(values["diluted_eps"], 0)
        json.dumps(result, allow_nan=False)

    def test_failure_is_unavailable_and_does_not_leak_exception(self):
        loader = Mock(side_effect=RuntimeError("sensitive_internal_detail"))
        result = data.load_snapshot("PETR4", loader, now=NOW)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["provider_used"])
        self.assertIn("Yahoo Finance", " ".join(result["warnings"]))
        self.assertNotIn("sensitive_internal_detail", json.dumps(result))
        loader.assert_called_once_with(SYMBOL)

    def test_partial_data_stays_yahoo(self):
        raw = payload()
        raw["balance_sheet"] = {}
        result = self.load(raw)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["provider_used"], "yfinance")
        self.assertEqual(result["quote"]["price"], 32.51)
        self.assertTrue(result["statements"]["income_statement"])
        self.loader.assert_called_once()

    def test_empty_response_is_unavailable(self):
        result = self.load({})
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("Yahoo Finance (dados indisponíveis)", data.render_data_report(result))

    def test_unknown_currency_not_assumed_brl(self):
        result = self.load(payload(currency=None))
        self.assertFalse(result["fundamentals_available"])
        self.assertIsNone(result["statements"]["income_statement"][0]["currency"])

    def test_mismatched_currencies_or_periods_not_combined(self):
        for change in ("currency", "period"):
            raw = payload()
            if change == "currency":
                raw["statement_metadata"]["balance_sheet"]["2025-12-31"]["currency"] = "USD"
            else:
                raw["balance_sheet"]["2024-12-31"] = raw["balance_sheet"].pop("2025-12-31")
                raw["statement_metadata"]["balance_sheet"]["2024-12-31"] = raw["statement_metadata"]["balance_sheet"].pop("2025-12-31")
            result = self.load(raw)
            self.assertFalse(result["fundamentals_available"])
            self.assertIsNone(result["common_period"])

    def test_wrong_symbol_and_quarterly_rows_are_discarded(self):
        for field, value in (("symbol", "PBR"), ("period", "Q4")):
            raw = payload()
            raw["statement_metadata"]["income_statement"]["2025-12-31"][field] = value
            result = self.load(raw)
            self.assertEqual(result["statements"]["income_statement"], [])
            self.assertFalse(result["fundamentals_available"])

    def test_usd_other_symbol_or_other_source_quote_is_discarded(self):
        for field, value in (("currency", "USD"), ("symbol", "PBR"), ("source", "other")):
            raw = payload()
            raw["quote"][field] = value
            self.assertIsNone(self.load(raw)["quote"])

    def test_stale_or_undated_quote_is_partial_without_source_switch(self):
        for time in (None, "2025-01-01T00:00:00+00:00", "2027-01-01T00:00:00+00:00"):
            raw = payload()
            raw["quote"]["as_of"] = time
            result = self.load(raw)
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["provider_used"], "yfinance")
            self.assertTrue(result["warnings"])
            self.loader.assert_called_once()

    def test_old_statements_are_partial(self):
        result = self.load(payload(end="2023-12-31"))
        self.assertEqual(result["status"], "partial")
        self.assertIn("550 dias", " ".join(result["warnings"]))

    def test_no_common_equity_substitution(self):
        raw = payload()
        raw["balance_sheet"]["2025-12-31"] = {"Common Stock Equity": 2000}
        result = self.load(raw)
        self.assertIsNone(result["statements"]["balance_sheet"][0]["values"]["stockholders_equity"])

    def test_report_localisation_and_missing_fields(self):
        report = data.render_data_report(self.load())
        for expected in ("PETR4", "B3", "R$ 32,51", "1.000,00", "-100,00", "0,00", "Não disponível", "BRL", "Yahoo Finance", "2025-12-31"):
            self.assertIn(expected, report)
        self.assertNotIn("Total Revenue", report)
        self.assertNotIn("Seleção da fonte", report)

    def test_public_tool_uses_only_yahoo(self):
        with patch.object(server, "_get_financial_statements_yfinance", return_value=payload()) as fetch:
            result = server.get_financial_statements("petr4")
            self.assertEqual(result["schema_version"], "3.1")
            self.assertNotIn("selection", result)
            fetch.assert_called_once_with(SYMBOL)

    def test_removed_provider_argument_is_not_silently_accepted(self):
        with self.assertRaises(TypeError):
            server.get_financial_statements("PETR4", provider="other")


if __name__ == "__main__":
    unittest.main()
