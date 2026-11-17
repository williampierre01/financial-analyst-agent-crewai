import unittest
from copy import deepcopy
from datetime import datetime, timezone
from operating_validation import evidence_digest, validate_observation, validate_batch

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


class OperatingValidationTests(unittest.TestCase):
    def setUp(self):
        self.observation = dict(ticker='PETR4.SA', period_end='2025-12-31',
            period_type='annual', currency='USD', unit='currency_units', value=26113000000,
            source='Yahoo fundamentals-timeseries', source_field='annualTotalOperatingIncomeAsReported',
            retrieved_at='2026-11-16T00:00:00+00:00')
        self.official = dict(ticker='PETR4.SA', period_end='2025-12-31', period_type='annual',
            currency='USD', value=26113, scale=1000000, precision=1, perimeter='consolidated',
            measure='operating_income_reported', unresolved_restatement=False,
            document=dict(url='https://example.org/fixture', version='fixture-v1',
                          location='table 1', sha256='a'*64))

    def review(self):
        return dict(evidence_digest=evidence_digest(self.observation, self.official),
            rule_version='1', reviewer='test-reviewer', decision='approved',
            reviewed_at='2026-11-16T01:00:00+00:00')

    def check(self, reviews=None):
        return validate_observation(self.observation, self.official,
            reviews=[self.review()] if reviews is None else reviews, now=NOW)

    def test_exact_boundary_and_outside(self):
        for offset, status in ((0, 'validated'), (500000, 'validated'), (500001, 'rejected')):
            self.observation['value'] = 26113000000 + offset
            result = self.check()
            self.assertEqual(result['status'], status)
            self.assertFalse(result['eligible_for_analysis'])

    def test_zero_and_negative(self):
        for value in (0, -1000000):
            self.observation['value'] = value
            self.official['value'] = value / 1000000
            self.assertEqual(self.check()['status'], 'validated')

    def test_invalid_values(self):
        for value in (None, True, float('nan'), float('inf')):
            self.observation['value'] = value
            self.assertEqual(self.check(reviews=[])['status'], 'rejected')

    def test_incompatible_metadata(self):
        original = deepcopy(self.observation)
        for key, value in [('currency', 'BRL'), ('ticker', 'VALE3.SA'),
                           ('period_end', '2024-12-31'), ('unit', 'millions'),
                           ('source_field', 'annualOperatingIncome'), ('period_type', 'quarterly')]:
            self.observation = {**original, key: value}
            self.assertEqual(self.check()['status'], 'rejected', key)

    def test_official_constraints(self):
        original = deepcopy(self.official)
        for key, value in [('scale', 0), ('precision', -1), ('perimeter', 'segment'),
                           ('measure', 'adjusted_operating_income')]:
            self.official = {**original, key: value}
            self.assertEqual(self.check()['status'], 'rejected', key)

    def test_missing_evidence_review_and_forged_flags(self):
        self.observation['eligible_for_analysis'] = True
        self.observation['validation_status'] = 'validated'
        self.assertEqual(self.check(reviews=[])['status'], 'unverified')
        self.assertFalse(self.check(reviews=[])['eligible_for_analysis'])
        self.assertEqual(validate_observation(self.observation, now=NOW)['status'], 'unverified')
        self.official['document'] = {}
        self.assertEqual(self.check()['status'], 'unverified')

    def test_changed_version_invalidates_review(self):
        review = self.review()
        self.official['document']['version'] = 'v2'
        self.assertEqual(self.check([review])['status'], 'unverified')

    def test_future_period_and_unresolved_restatement(self):
        self.official['unresolved_restatement'] = True
        self.assertEqual(self.check()['status'], 'unverified')
        self.official['period_end'] = self.observation['period_end'] = '2027-12-31'
        self.assertEqual(self.check()['status'], 'rejected')

    def test_duplicates_and_year_isolation(self):
        obs = self.observation
        same = validate_batch([obs, deepcopy(obs)], [self.official], reviews=[self.review()], now=NOW)
        self.assertTrue(all(r['status'] == 'validated' for r in same))
        conflict = validate_batch([obs, {**obs, 'value': 1}], [self.official], now=NOW)
        self.assertTrue(all(r['status'] == 'rejected' for r in conflict))
        other_year = {**obs, 'period_end': '2024-12-31'}
        results = validate_batch([obs, other_year], [self.official], reviews=[self.review()], now=NOW)
        self.assertEqual([r['status'] for r in results], ['validated', 'unverified'])

    def test_malformed_document_and_review_do_not_crash(self):
        self.official['document'] = None
        self.assertEqual(self.check(reviews=[])['status'], 'rejected')
        self.setUp()
        review = self.review()
        review['reviewed_at'] = 'invalid'
        self.assertEqual(self.check([None, review])['status'], 'unverified')

    def test_real_candidates_remain_unapproved(self):
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / 'docs/evidencias/operating-review-candidates.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        results = validate_batch(data['observations'], data['official_records'], reviews=data['reviews'], now=datetime(2026, 11, 18, tzinfo=timezone.utc))
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r['status'] == 'unverified' and not r['eligible_for_analysis'] for r in results))

