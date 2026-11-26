"""Server-owned documentary registry. Client/provider approval flags are ignored."""
import hashlib
import json
from pathlib import Path

from operating_validation import validate_batch

ROOT = Path(__file__).resolve().parent
PACKAGE = 'docs/evidencias/operating-review-package-2026-11-26.json'
APPROVAL = 'docs/evidencias/operating-review-approval-2026-11-26.json'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _local_bytes(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Registry path outside repository')
    return path.read_bytes()


def approved_operating_income(ticker, end, currency, value, now):
    """Match a fresh reported observation to the exact reviewed server evidence.

    Failure never falls back to another field or to the stored candidate value.
    Read on each request so removing approval or changing evidence revokes use.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        raw = _local_bytes(ROOT, PACKAGE)
        package = json.loads(raw)
        approval = json.loads(_local_bytes(ROOT, APPROVAL))
        if approval['package_sha256'] != _sha(raw):
            return None
        scope = package['review_scope']
        if approval['scope_sha256'] != scope['sha256'] or _sha(_local_bytes(ROOT, scope['path'])) != scope['sha256']:
            return None
        for name, expected in package['supporting_evidence'].items():
            if _sha(_local_bytes(ROOT, 'docs/evidencias/' + name)) != expected:
                return None
        reviews = [r for r in approval['reviews'] if r.get('scope_accepted') is True]
        results = validate_batch(package['observations'], package['official_records'], reviews=reviews, now=now)
        for observation, result in zip(package['observations'], results):
            if (result['status'] == 'validated' and observation['ticker'] == ticker
                    and observation['period_end'] == end and observation['currency'] == currency
                    and observation['value'] == value):
                official = next(r for r in package['official_records']
                                if r['ticker'] == ticker and r['period_end'] == end)
                return {'value': value, 'source_field': observation['source_field'],
                        'document_url': official['document']['url'],
                        'document_location': official['document']['location'],
                        'evidence_digest': result['evidence_digest'],
                        'reviewed_at': next(r['reviewed_at'] for r in reviews
                                            if r['evidence_digest'] == result['evidence_digest']),
                        'scope': 'Revisão documental com alcance limitado; não constitui auditoria.'}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, StopIteration):
        return None
    return None
