import unittest
from copy import deepcopy

from financial_data import load_snapshot
from report_guidance import presentation_references
from test_yahoo_contract import NOW, payload


class PresentationReferencesTests(unittest.TestCase):
    def snapshot(self, ticker, currency="BRL"):
        raw = payload(currency=currency)
        raw["quote"]["symbol"] = ticker + ".SA"
        for periods in raw["statement_metadata"].values():
            for period in periods.values():
                period["symbol"] = ticker + ".SA"
        return load_snapshot(ticker, lambda _: raw, now=NOW)

    def test_formats_totals_and_per_share_without_mutation(self):
        for ticker in ("PETR4", "VALE3", "ITUB4"):
            data = self.snapshot(ticker)
            period = data["statements"]["income_statement"][0]
            period["values"].update(revenue=19_634_000_000, net_income=-1_500_000,
                                    diluted_eps=1.52, operating_income=0)
            original = deepcopy(data)
            text = presentation_references(data)
            self.assertIn("R$ 19.634,00 mi", text)
            self.assertIn("R$ -1,50 mi", text)
            self.assertIn("R$ 1,52 por ação", text)
            self.assertIn("R$ 0,00", text)
            self.assertIn("período encerrado em 2025-12-31", text)
            self.assertIn("Yahoo Finance (via yfinance)", text)
            self.assertEqual(data, original)

    def test_unknown_and_foreign_currency_and_missing_values(self):
        for currency, expected in ((None, "moeda não informada"), ("USD", "USD")):
            data = self.snapshot("VALE3", currency)
            text = presentation_references(data)
            self.assertIn(f"{expected} 1.000,00", text)
            self.assertNotIn("R$", text)
            self.assertIn("Não disponível", text)

    def test_no_snapshot(self):
        self.assertIn("Sem referência", presentation_references(None))
