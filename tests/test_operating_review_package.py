"""The documentary draft must not silently become an approved runtime source."""
import json
import hashlib
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from operating_validation import evidence_digest, validate_batch

EVIDENCE = Path(__file__).resolve().parents[1] / 'docs' / 'evidencias'


class OperatingReviewPackageTests(unittest.TestCase):
    def setUp(self):
        self.package = json.loads((EVIDENCE / 'operating-review-package-2026-11-25-draft.json').read_text(encoding='utf-8'))

    def test_versioned_references_preserve_original_observations(self):
        original = json.loads((EVIDENCE / 'operating-review-candidates.json').read_text(encoding='utf-8'))
        annual = json.loads((EVIDENCE / 'annual-source-verification-2026-11-24.json').read_text(encoding='utf-8'))
        refs = {r['ticker']: r for r in annual['records']}
        self.assertEqual(self.package['observations'], original['observations'])
        self.assertEqual(len(self.package['official_records']), 4)
        for official in self.package['official_records']:
            reference = refs[official['ticker']]
            self.assertEqual(official['document']['sha256'], reference['sha256'])
            self.assertEqual(official['document']['url'], reference['url'])
            self.assertEqual(official['value'], reference['values'][reference['periods'].index(official['period_end'])])

    def test_draft_is_blocked_even_with_a_synthetic_review(self):
        package = self.package
        self.assertEqual(package['reviews'], [])
        reviews = []
        for obs, official, recorded in zip(package['observations'], package['official_records'], package['evidence_digests']):
            self.assertEqual(recorded['digest'], evidence_digest(obs, official))
            self.assertIsNone(official['unresolved_restatement'])
            # Test-only attacker input: an approval cannot resolve incomplete coverage.
            reviews.append(dict(evidence_digest=recorded['digest'], rule_version='1',
                reviewer='synthetic-test-only', decision='approved',
                reviewed_at='2026-11-25T19:00:00+00:00'))
        for supplied_reviews in ([], reviews):
            results = validate_batch(package['observations'], package['official_records'],
                reviews=supplied_reviews, now=datetime(2026, 11, 26, tzinfo=timezone.utc))
            self.assertEqual(len(results), 4)
            self.assertTrue(all(r['status'] == 'unverified' and not r['eligible_for_analysis'] for r in results))

    def test_finishing_assessment_requires_new_digest(self):
        package = self.package
        for observation, official, recorded in zip(package['observations'], package['official_records'], package['evidence_digests']):
            changed = deepcopy(official)
            changed['unresolved_restatement'] = False
            self.assertNotEqual(evidence_digest(observation, changed), recorded['digest'])

    def test_review_ready_package_is_bound_to_scope_and_sources(self):
        package = json.loads((EVIDENCE / 'operating-review-package-2026-11-26.json').read_text(encoding='utf-8'))
        repo = EVIDENCE.parents[1]
        scope = package['review_scope']
        self.assertEqual(hashlib.sha256((repo / scope['path']).read_bytes()).hexdigest(), scope['sha256'])
        for name, expected in package['supporting_evidence'].items():
            self.assertEqual(hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest(), expected, name)
        manifest_digest = hashlib.sha256(json.dumps(package['supporting_evidence'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        for obs, official, recorded in zip(package['observations'], package['official_records'], package['evidence_digests']):
            self.assertEqual(official['assessment']['scope'], scope)
            self.assertEqual(official['assessment']['supporting_evidence_digest'], manifest_digest)
            self.assertEqual(evidence_digest(obs, official), recorded['digest'])
            changed = deepcopy(official)
            changed['assessment']['scope']['sha256'] = '0' * 64
            self.assertNotEqual(evidence_digest(obs, changed), recorded['digest'])

    def test_review_ready_package_still_requires_human_review(self):
        package = json.loads((EVIDENCE / 'operating-review-package-2026-11-26.json').read_text(encoding='utf-8'))
        self.assertEqual(package['reviews'], [])
        results = validate_batch(package['observations'], package['official_records'],
            reviews=package['reviews'], now=datetime(2026, 11, 27, tzinfo=timezone.utc))
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertEqual(result['reason'], 'missing_matching_review')
            self.assertEqual(result['status'], 'unverified')
            self.assertFalse(result['eligible_for_analysis'])
