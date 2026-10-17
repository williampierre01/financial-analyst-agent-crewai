import json
import unittest
from copy import deepcopy

from financial_data import load_snapshot
from test_yahoo_contract import NOW, payload
from verified_metrics import calculate_metrics


def sample():
    data = load_snapshot("PETR4", lambda _: payload(), now=NOW)
    income = data["statements"]["income_statement"][0]
    income["values"].update(net_income=2352e6, revenue=38403e6, diluted_eps=.55)
    balance = data["statements"]["balance_sheet"][0]
    balance["values"].update(stockholders_equity=33509e6, total_debt=21801e6)
    for group in ("income_statement", "balance_sheet"):
        previous = deepcopy(data["statements"][group][0])
        previous["period_end"] = "2024-12-31"
        data["statements"][group].append(previous)
    data["statements"]["income_statement"][1]["values"]["net_income"] = 6166e6
    data["statements"]["balance_sheet"][1]["values"]["stockholders_equity"] = 33406e6
    data["quote"]["price"] = 66.21
    return data


def find(data, name, end="2025-12-31"):
    return next(r for r in calculate_metrics(data) if r["name"] == name and r["period_end"] == end)


class VerifiedMetricsTests(unittest.TestCase):
    def test_example_arithmetic_references_and_no_mutation(self):
        data = sample()
        original = deepcopy(data)
        self.assertAlmostEqual(find(data, "ROE sobre patrimônio de encerramento")["value"], 2352 / 33509 * 100)
        avg = find(data, "ROE sobre média de dois saldos")
        self.assertAlmostEqual(avg["value"], 2352 / ((33406 + 33509) / 2) * 100)
        self.assertEqual([i["period_end"] for i in avg["inputs"]], ["2025-12-31", "2024-12-31", "2025-12-31"])
        self.assertAlmostEqual(find(data, "Margem líquida")["value"], 2352 / 38403 * 100)
        self.assertAlmostEqual(find(data, "Dívida/patrimônio")["value"], 21801 / 33509 * 100)
        self.assertAlmostEqual(find(data, "P/L")["value"], 66.21 / .55)
        self.assertAlmostEqual(find(data, "ROE sobre patrimônio de encerramento", "2024-12-31")["value"], 6166 / 33406 * 100)
        self.assertEqual(find(data, "ROE sobre média de dois saldos", "2024-12-31")["status"], "unavailable")
        self.assertEqual(len([r for r in calculate_metrics(data) if r["name"] == "P/L"]), 1)
        json.dumps(calculate_metrics(data), allow_nan=False)
        self.assertEqual(data, original)

    def test_missing_cash_flow_does_not_block_supported_metrics(self):
        data = sample()
        data["statements"]["cash_flow"] = []
        data["common_period"] = None
        data["fundamentals_available"] = False
        self.assertEqual(find(data, "ROE sobre média de dois saldos")["status"], "calculated")

    def test_opening_must_be_adjacent_unique_and_compatible(self):
        for change in ("gap", "missing", "duplicate", "currency", "source", "unit", "period_type"):
            data = sample()
            rows = data["statements"]["balance_sheet"]
            if change == "gap":
                rows[1]["period_end"] = "2023-12-31"
            elif change == "missing":
                rows.pop()
            elif change == "duplicate":
                rows.append(deepcopy(rows[1]))
            else:
                rows[1][change] = {"currency": "USD", "source": "other", "unit": "millions", "period_type": "quarterly"}[change]
            with self.subTest(change=change):
                self.assertEqual(find(data, "ROE sobre média de dois saldos")["status"], "unavailable")

    def test_unknown_currency_and_incompatible_current_period(self):
        for key, value in (("currency", None), ("currency", "USD"), ("source", None),
                           ("source", "other"), ("period_end", "2025-06-30")):
            data = sample()
            data["statements"]["balance_sheet"][0][key] = value
            with self.subTest(key=key, value=value):
                self.assertEqual(find(data, "ROE sobre patrimônio de encerramento")["status"], "unavailable")

    def test_foreign_statements_valid_but_no_mixed_currency_pl(self):
        data = sample()
        for rows in data["statements"].values():
            for row in rows:
                row["currency"] = "USD"
        self.assertEqual(find(data, "ROE sobre média de dois saldos")["status"], "calculated")
        self.assertEqual(find(data, "P/L")["status"], "unavailable")

    def test_invalid_denominators_and_missing_values(self):
        for value in (0, -1, None, float("nan"), float("inf")):
            data = sample()
            data["statements"]["balance_sheet"][0]["values"]["stockholders_equity"] = value
            for name in ("ROE sobre patrimônio de encerramento", "ROE sobre média de dois saldos", "Dívida/patrimônio"):
                with self.subTest(value=value, name=name):
                    self.assertEqual(find(data, name)["status"], "unavailable")
            data["statements"]["income_statement"][0]["values"]["diluted_eps"] = value
            self.assertEqual(find(data, "P/L")["status"], "unavailable")

    def test_losses_and_zero_profit_are_preserved(self):
        for value in (-100, 0):
            data = sample()
            data["statements"]["income_statement"][0]["values"]["net_income"] = value
            result = find(data, "ROE sobre patrimônio de encerramento")
            self.assertEqual(result["status"], "calculated")
            self.assertAlmostEqual(result["value"], value / 33509e6 * 100)

    def test_quote_unavailable_stale_or_undated(self):
        for quote in (None, {**sample()["quote"], "freshness": "stale"},
                      {**sample()["quote"], "as_of": None}):
            data = sample()
            data["quote"] = quote
            self.assertEqual(find(data, "P/L")["status"], "unavailable")

    def test_empty_snapshot(self):
        self.assertEqual(calculate_metrics(None), [])
        self.assertEqual(calculate_metrics({}), [])

    def test_missing_income_reports_pl_unavailable_without_borrowing_balance_date(self):
        data = sample()
        data["statements"]["income_statement"] = []
        original = deepcopy(data)
        result = find(data, "P/L", None)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["value"])
        self.assertIn("Demonstrativo de resultados anual ausente", result["reason"])
        self.assertEqual(result["inputs"][0]["value"], 66.21)
        self.assertIsNone(result["inputs"][1])
        self.assertEqual(find(data, "Dívida/patrimônio")["status"], "calculated")
        self.assertEqual(data, original)

    def test_quote_only_reports_all_unavailable_without_inventing_periods(self):
        data = sample()
        data["statements"] = {}
        original = deepcopy(data)
        results = calculate_metrics(data)
        self.assertEqual({r["name"] for r in results}, {
            "P/L", "Margem líquida", "Dívida/patrimônio",
            "ROE sobre patrimônio de encerramento", "ROE sobre média de dois saldos"})
        for result in results:
            self.assertEqual(result["status"], "unavailable")
            self.assertIsNone(result["value"])
            self.assertIsNone(result["period_end"])
            self.assertTrue(result["reason"])
        json.dumps(results, allow_nan=False)
        self.assertEqual(data, original)

    def test_duplicate_latest_income_does_not_silently_drop_pl(self):
        data = sample()
        data["statements"]["income_statement"].append(
            deepcopy(data["statements"]["income_statement"][0]))
        result = find(data, "P/L")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("ambíguo", result["reason"])
