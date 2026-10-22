"""Unreconciled provider fields cannot reach the model as financial facts."""
import unittest
from copy import deepcopy
import json

from financial_data import normalize_snapshot, render_data_report
from report_guidance import presentation_references
from verified_metrics import calculate_metrics
from test_yahoo_contract import payload, NOW, SYMBOL


class OperatingIncomeGuardTests(unittest.TestCase):
    def test_withholds_value_without_mutating_source_or_other_metrics(self):
        for value in (11_343_000_000, 27_758_000_000, 0, -123):
            raw = payload()
            raw["income_statement"]["2025-12-31"]["Operating Income"] = value
            original = deepcopy(raw)
            result = normalize_snapshot(raw, SYMBOL, NOW)
            self.assertIsNone(result["statements"]["income_statement"][0]["values"]["operating_income"])
            self.assertEqual(raw, original)
            self.assertEqual(calculate_metrics(result), calculate_metrics(normalize_snapshot(payload(), SYMBOL, NOW)))
            self.assertEqual(result["status"], "partial")
            self.assertTrue(any("conciliada" in warning for warning in result["warnings"]))

    def test_all_periods_are_guarded_and_references_have_no_value(self):
        raw = payload()
        raw["income_statement"]["2024-12-31"] = {"Operating Income": 11_101_000_000}
        raw["statement_metadata"]["income_statement"]["2024-12-31"] = {
            "currency": "BRL", "symbol": SYMBOL, "period": "FY"}
        raw["income_statement"]["2025-12-31"]["Operating Income"] = 11_343_000_000
        result = normalize_snapshot(raw, SYMBOL, NOW)
        for row in result["statements"]["income_statement"]:
            self.assertIsNone(row["values"]["operating_income"])
        for text in (json.dumps(result), presentation_references(result), render_data_report(result)):
            self.assertNotIn("11343000000", text)
            self.assertNotIn("11.343,00", text)
            self.assertNotIn("11.101,00", text)
