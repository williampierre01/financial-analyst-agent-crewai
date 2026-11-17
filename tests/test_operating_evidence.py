import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from financial_data import normalize_snapshot
from operating_evidence import collect_reported_operating_income
from test_yahoo_contract import NOW, SYMBOL, payload


class OperatingEvidenceTests(unittest.TestCase):
    def collect(self, value=26113000000, currency="USD", symbol=SYMBOL, period="12M", extra=None):
        point = {"asOfDate": "2025-12-31", "periodType": period,
                 "currencyCode": currency, "reportedValue": {"raw": value}}
        points = [point] + (extra or [])
        client = SimpleNamespace(_data=Mock())
        client._data.cache_get.return_value.json.return_value = {
            "timeseries": {"result": [{"meta": {"symbol": [symbol]},
                "annualTotalOperatingIncomeAsReported": points}]}}
        result = collect_reported_operating_income(client, SYMBOL, now=NOW)
        url = client._data.cache_get.call_args.kwargs["url"]
        self.assertIn("annualTotalOperatingIncomeAsReported", url)
        self.assertNotIn("annualOperatingIncome", url)
        return result

    def test_preserves_zero_negative_and_provenance_but_never_approves(self):
        for value in (26113000000, 0, -123):
            result = self.collect(value)
            self.assertEqual(result["observations"][0]["value"], value)
            self.assertEqual(result["observations"][0]["currency"], "USD")
            self.assertFalse(result["eligible_for_analysis"])
            self.assertEqual(result["validation_status"], "unverified")

    def test_rejects_missing_invalid_or_incompatible_observations(self):
        for kwargs in ({"value": None}, {"value": float("nan")}, {"value": True},
                       {"currency": None}, {"symbol": "VALE3.SA"}, {"period": "3M"}):
            self.assertEqual(self.collect(**kwargs)["observations"], [])

    def test_conflicting_duplicate_raises(self):
        with self.assertRaises(ValueError):
            self.collect(extra=[{"asOfDate": "2025-12-31", "periodType": "12M",
                "currencyCode": "USD", "reportedValue": {"raw": 1}}])

    def test_conflicting_currency_is_not_usable(self):
        result = self.collect(extra=[{"asOfDate": "2025-12-31", "periodType": "12M",
            "currencyCode": "BRL", "reportedValue": {"raw": 26113000000}}])
        self.assertEqual(result["observations"], [])

    def test_evidence_cannot_enter_public_snapshot(self):
        raw = payload()
        raw["operating_evidence"] = self.collect()
        raw["income_statement"]["2025-12-31"]["Total Operating Income As Reported"] = 26113000000
        result = normalize_snapshot(raw, SYMBOL, NOW)
        self.assertNotIn("26113000000", json.dumps(result))
        self.assertNotIn("operating_evidence", result)
        self.assertIsNone(result["statements"]["income_statement"][0]["values"]["operating_income"])
