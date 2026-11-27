import unittest
from copy import deepcopy
from grounding import operating_availability


class OperatingContextTests(unittest.TestCase):
    def test_availability_is_per_period_and_preserves_zero_and_references(self):
        approved = {"period_end": "2025-12-31", "currency": "USD",
                    "values": {"operating_income": None, "reported_operating_income": 0},
                    "reported_operating_income_reference": {"value": 0, "document_url": "https://example.org/annual"}}
        missing = {"period_end": "2024-12-31", "currency": "USD", "values": {"operating_income": None}}
        data = {"statements": {"income_statement": [approved, missing]}}
        before = deepcopy(data)
        result = operating_availability(data)
        self.assertEqual(result[0]["reported_operating_income_status"], "disponível com referência documental")
        self.assertEqual(result[0]["reference"], approved["reported_operating_income_reference"])
        self.assertEqual(result[1]["reported_operating_income_status"], "indisponível nesta base")
        self.assertIsNone(result[1]["reference"])
        self.assertEqual(data, before)
        approved["reported_operating_income_reference"]["value"] = 1
        self.assertEqual(operating_availability(data)[0]["reported_operating_income_status"], "indisponível nesta base")

    def test_missing_snapshot_has_no_invented_periods(self):
        self.assertEqual(operating_availability(None), [])
        self.assertEqual(operating_availability({"statements": {}}), [])
