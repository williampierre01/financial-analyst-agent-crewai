import json
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch

import operating_registry as registry
from financial_data import normalize_snapshot, render_data_report
from report_guidance import presentation_references
from backend.api.schemas import FinancialSnapshot
from test_yahoo_contract import payload

NOW = datetime(2026, 11, 27, tzinfo=timezone.utc)


class OperatingRegistryTests(unittest.TestCase):
    def test_only_exact_reviewed_observations_match(self):
        cases = [('PETR4.SA', '2025-12-31', 26113000000),
                 ('PETR4.SA', '2024-12-31', 26876000000),
                 ('VALE3.SA', '2025-12-31', 5897000000),
                 ('VALE3.SA', '2024-12-31', 10788000000)]
        for ticker, end, value in cases:
            self.assertIsNotNone(registry.approved_operating_income(ticker, end, 'USD', value, NOW))
            for changed in (value + 1, None, True, float('nan'), float('inf')):
                self.assertIsNone(registry.approved_operating_income(ticker, end, 'USD', changed, NOW))
            self.assertIsNone(registry.approved_operating_income(ticker, end, 'BRL', value, NOW))
            self.assertIsNone(registry.approved_operating_income('ITUB4.SA', end, 'USD', value, NOW))
        self.assertIsNone(registry.approved_operating_income('PETR4.SA', '2023-12-31', 'USD', 26113000000, NOW))

    def test_revocation_and_changed_package_fail_closed(self):
        read = registry._local_bytes
        for mode in ('missing', 'revoked', 'package_changed', 'scope_changed'):
            def altered(root, path):
                content = read(root, path)
                if mode == 'missing' and path == registry.APPROVAL:
                    raise FileNotFoundError()
                if mode == 'revoked' and path == registry.APPROVAL:
                    data = json.loads(content)
                    data['reviews'] = []
                    return json.dumps(data).encode()
                if mode == 'package_changed' and path == registry.PACKAGE:
                    return content + b' '
                if mode == 'scope_changed' and path.endswith('revisao-final-operacional-2026-11-26.md'):
                    return content + b'changed'
                return content
            with patch.object(registry, '_local_bytes', side_effect=altered):
                self.assertIsNone(registry.approved_operating_income('PETR4.SA', '2025-12-31', 'USD', 26113000000, NOW), mode)

    def test_contract_report_and_ai_receive_reported_value_with_source(self):
        raw = payload()
        for group in raw['statement_metadata'].values():
            for meta in group.values():
                meta['currency'] = 'USD'
        raw['income_statement']['2025-12-31']['Total Operating Income As Reported'] = 26113000000
        raw['income_statement']['2025-12-31']['Operating Income'] = 999999999
        original = deepcopy(raw)
        result = normalize_snapshot(raw, 'PETR4.SA', NOW)
        self.assertEqual(raw, original)
        period = result['statements']['income_statement'][0]
        self.assertIsNone(period['values']['operating_income'])
        self.assertEqual(period['values']['reported_operating_income'], 26113000000)
        self.assertEqual(result['schema_version'], '3.1')
        encoded = FinancialSnapshot.model_validate(result).model_dump(mode='json')
        self.assertTrue(encoded['statements']['income_statement'][0]['reported_operating_income_reference']['document_url'].startswith('https://www.sec.gov/'))
        for text in (render_data_report(result), presentation_references(result)):
            self.assertIn('Resultado operacional reportado', text)
            self.assertIn('https://www.sec.gov/', text)
            self.assertNotIn('999999999', text)

    def test_external_flags_and_missing_field_cannot_restore_value(self):
        raw = payload()
        raw['operating_evidence'] = {'eligible_for_analysis': True, 'validation_status': 'validated'}
        raw['income_statement']['2025-12-31']['Operating Income'] = 26113000000
        result = normalize_snapshot(raw, 'PETR4.SA', NOW)
        row = result['statements']['income_statement'][0]
        self.assertIsNone(row['values']['reported_operating_income'])
        self.assertNotIn('reported_operating_income_reference', row)
        self.assertNotIn('26113000000', json.dumps(result))
