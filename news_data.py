"""Conservative provenance for search results, not verification of articles."""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


def news_url(value) -> str | None:
    """Keep the returned HTTP(S) link; never synthesize a publisher URL."""
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme not in {"http", "https"} or not parts.hostname
                or parts.username is not None or parts.password is not None):
            return None
        _ = parts.port  # Reject malformed ports too.
        return value
    except ValueError:
        return None


def news_date(value, retrieved_at: datetime) -> dict:
    """Accept only ISO datetimes with timezone; no guesses from titles or URLs.

    A parseable date remains search-provider metadata, not a verified publication
    date. Date-only/naive values cannot establish a publication instant.
    """
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must include timezone")
    raw = value if isinstance(value, str) else None
    result = {"date_raw": raw, "published_at": None, "date_status": "missing",
              "date_label": "Data de publicação não confirmada (não informada pela busca)."}
    if value is None or value == "":
        return result
    try:
        if raw is None:
            raise ValueError("unsupported date type")
        parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        result.update(date_status="invalid", date_label=
                      "Data de publicação não confirmada (formato não reconhecido).")
        return result
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        result.update(date_status="timezone_missing", date_label=
                      "Data de publicação não confirmada (horário ou fuso não informado).")
        return result
    try:
        utc = parsed.astimezone(timezone.utc)
        local = utc.astimezone(ZoneInfo("America/Sao_Paulo"))
    except (ValueError, OverflowError):
        result.update(date_status="invalid", date_label=
                      "Data de publicação não confirmada (data fora do intervalo suportado).")
        return result
    if utc > retrieved_at.astimezone(timezone.utc):
        result.update(date_status="future", date_label=
                      "Data de publicação não confirmada (data futura informada pela busca).")
        return result
    result.update(published_at=utc.isoformat(), date_status="reported", date_label=
                  local.strftime("%d/%m/%Y %H:%M") +
                  " (Brasília; data informada pela busca, não verificada na publicação).")
    return result


def order_news(items, retrieved_at):
    """Order reported instants; label old/undated context without inventing dates."""
    cutoff = retrieved_at - timedelta(days=30)
    for item in items:
        if item.published_at:
            published = datetime.fromisoformat(item.published_at)
            if published < cutoff:
                item.date_label = "Contexto histórico (mais de 30 dias): " + item.date_label
        else:
            item.date_label = "Atualidade não confirmada: " + item.date_label
    return sorted(items, key=lambda item: item.published_at or "", reverse=True)
