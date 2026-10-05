"""Compact, date-scoped daily result storage for the user's browser cookie."""

import base64
import binascii
import gzip
import json
import zlib
from datetime import datetime, time, timedelta

from app.config import APP_TIMEZONE
from app.schemas import Article, TrendReport

COOKIE_NAME = "tech_news_daily_v1"
MAX_COOKIE_VALUE_LENGTH = 3600
MAX_DECOMPRESSED_BYTES = 128_000


def today_key() -> str:
    return datetime.now(APP_TIMEZONE).date().isoformat()


def cookie_expiration() -> datetime:
    tomorrow = datetime.now(APP_TIMEZONE).date() + timedelta(days=1)
    return datetime.combine(tomorrow, time.min, tzinfo=APP_TIMEZONE)


def _pack(payload: dict) -> str:
    encoded_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(encoded_json, mtime=0)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def encode_daily_result(result: dict, day: str | None = None) -> tuple[str, bool]:
    """Return cookie value and whether the displayed digest had to be shortened."""
    article_values = [
        article.model_dump(mode="json") if isinstance(article, Article) else article
        for article in result.get("tech_articles", [])
    ]
    trend = result.get("trend_report")
    trend_value = trend.model_dump(mode="json") if isinstance(trend, TrendReport) else trend
    payload = {
        "day": day or today_key(),
        "summary": result.get("summary", ""),
        "trend_report": trend_value,
        "tech_articles": article_values,
        "articles_count": len(result.get("articles", [])),
        "tech_article_count": len(result.get("tech_articles", [])),
        "searched_feeds": result.get("searched_feeds", []),
        "research_notes": result.get("research_notes", []),
        "research_decision": result.get("research_decision", ""),
        "summary_truncated": False,
        "assessments_saved": True,
    }
    value = _pack(payload)
    if len(value) <= MAX_COOKIE_VALUE_LENGTH:
        return value, False

    # Keep the full digest and trend report whenever possible; assessments are
    # supplementary to that digest and may be too large for a browser cookie.
    payload["tech_articles"] = []
    payload["assessments_saved"] = False
    value = _pack(payload)
    if len(value) <= MAX_COOKIE_VALUE_LENGTH:
        return value, False

    # Browser cookies are small. Truncate at Markdown line boundaries so the
    # cache can still protect the daily token budget for unusually large digests.
    lines = str(payload.get("summary", "")).splitlines()
    low, high = 0, len(lines)
    best = ""
    while low <= high:
        middle = (low + high) // 2
        shortened = "\n".join(lines[:middle]).rstrip()
        if shortened:
            shortened += "\n\n*Digest shortened to fit browser-cookie storage.*"
        payload["summary"] = shortened
        payload["summary_truncated"] = True
        candidate = _pack(payload)
        if len(candidate) <= MAX_COOKIE_VALUE_LENGTH:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    if best:
        return best, True
    raise ValueError("Could not fit the daily news cache in a browser cookie")


def decode_daily_result(value: str | None, day: str | None = None) -> dict | None:
    """Validate and restore a cookie result for today; ignore malformed values."""
    if not value or len(value) > MAX_COOKIE_VALUE_LENGTH:
        return None
    try:
        padded = value + "=" * (-len(value) % 4)
        compressed = base64.b64decode(padded, altchars=b"-_", validate=True)
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        raw = decompressor.decompress(compressed, MAX_DECOMPRESSED_BYTES + 1)
        if len(raw) > MAX_DECOMPRESSED_BYTES or decompressor.unconsumed_tail:
            return None
        raw += decompressor.flush()
        if len(raw) > MAX_DECOMPRESSED_BYTES:
            return None
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("day") != (day or today_key()):
            return None
        payload["tech_articles"] = [Article.model_validate(item) for item in payload.get("tech_articles", [])]
        trend = payload.get("trend_report")
        payload["trend_report"] = TrendReport.model_validate(trend) if trend else None
        return payload
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, zlib.error, binascii.Error):
        return None
