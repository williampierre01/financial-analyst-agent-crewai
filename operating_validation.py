"""Offline documentary checks. No runtime app integration or authorization."""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal, DecimalException, InvalidOperation
from urllib.parse import urlsplit

RULE_VERSION = '1'


def evidence_digest(observation, official):
    """Bind review to the complete submitted evidence, including document version."""
    encoded = json.dumps([observation, official], sort_keys=True, ensure_ascii=False,
                         allow_nan=False, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def _number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError('invalid_number')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('invalid_number') from None
    if not result.is_finite():
        raise ValueError('invalid_number')
    return result


def validate_observation(observation, official=None, *, reviews=(), now=None):
    """Reviews must come from a separately maintained, trusted local register.

    This checks recorded assertions; it cannot authenticate a document or reviewer.
    Even a validated result is never eligible for production analysis here.
    """
    now = now or datetime.now(timezone.utc)
    result = {'status': 'unverified', 'reason': 'missing_official_evidence',
              'eligible_for_analysis': False, 'rule_version': RULE_VERSION}
    if not isinstance(observation, dict) or (official is not None and not isinstance(official, dict)):
        return {**result, 'status': 'rejected', 'reason': 'invalid_evidence_structure'}
    if not official:
        return result
    try:
        value = _number(observation.get('value'))
        scale = _number(official.get('scale'))
        precision = _number(official.get('precision'))
        official_value = _number(official.get('value')) * scale
        if scale <= 0 or precision < 0:
            raise ValueError('invalid_scale_or_precision')
        if observation.get('source_field') != 'annualTotalOperatingIncomeAsReported':
            raise ValueError('wrong_source_field')
        if observation.get('source') != 'Yahoo fundamentals-timeseries':
            raise ValueError('wrong_source')
        if observation.get('unit') != 'currency_units':
            raise ValueError('wrong_unit')
        for key in ('ticker', 'currency', 'period_end', 'period_type'):
            if not observation.get(key) or observation[key] != official.get(key):
                raise ValueError('incompatible_' + key)
        currency = observation['currency']
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isascii() or not currency.isupper() or not currency.isalpha():
            raise ValueError('invalid_currency')
        if observation['period_type'] != 'annual':
            raise ValueError('nonannual_period')
        if date.fromisoformat(observation['period_end']) > now.date():
            raise ValueError('future_period')
        collected = datetime.fromisoformat(observation['retrieved_at'])
        if collected.tzinfo is None or collected > now:
            raise ValueError('invalid_collection_time')
        if official.get('perimeter') != 'consolidated' or official.get('measure') != 'operating_income_reported':
            raise ValueError('incompatible_accounting_meaning')
        document = official.get('document', {})
        if not isinstance(document, dict):
            raise ValueError('invalid_document_structure')
        if not all(document.get(k) for k in ('url', 'version', 'location', 'sha256')):
            return {**result, 'reason': 'incomplete_document_reference'}
        url = urlsplit(document['url'])
        if url.scheme != 'https' or not url.netloc:
            raise ValueError('invalid_document_url')
        digest = document['sha256']
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid_document_digest')
        if official.get('unresolved_restatement') is not False:
            return {**result, 'reason': 'restatement_not_resolved'}
        difference = abs(value - official_value)
        tolerance = precision * scale / 2
        result.update(difference=str(difference), tolerance=str(tolerance))
        if difference > tolerance:
            raise ValueError('value_mismatch')
        fingerprint = evidence_digest(observation, official)
        result['evidence_digest'] = fingerprint
        for review in reviews:
            if not isinstance(review, dict):
                continue
            if review.get('evidence_digest') != fingerprint or review.get('rule_version') != RULE_VERSION:
                continue
            try:
                reviewed = datetime.fromisoformat(review.get('reviewed_at', ''))
            except (ValueError, TypeError):
                continue
            if (review.get('reviewer') and review.get('decision') == 'approved'
                    and reviewed.tzinfo is not None and collected <= reviewed <= now):
                return {**result, 'status': 'validated', 'reason': 'documentary_checks_passed'}
        return {**result, 'reason': 'missing_matching_review'}
    except (ValueError, TypeError, KeyError, OverflowError, DecimalException) as exc:
        return {**result, 'status': 'rejected', 'reason': str(exc) or 'invalid_evidence'}


def validate_batch(observations, official_records, *, reviews=(), now=None):
    """Conflicting duplicates cannot reuse an approval for one of their versions."""
    results = []
    for observation in observations:
        key = (observation.get('ticker'), observation.get('period_end'))
        peers = [o for o in observations if (o.get('ticker'), o.get('period_end')) == key]
        records = [o for o in official_records if (o.get('ticker'), o.get('period_end')) == key]
        if any(p != observation for p in peers) or any(r != records[0] for r in records[1:]):
            results.append({'status': 'rejected', 'reason': 'conflicting_duplicates',
                            'eligible_for_analysis': False, 'rule_version': RULE_VERSION})
        else:
            results.append(validate_observation(observation, records[0] if records else None,
                                                reviews=reviews, now=now))
    return results
