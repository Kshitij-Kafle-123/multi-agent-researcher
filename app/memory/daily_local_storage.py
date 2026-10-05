"""Lossless compressed daily result serialization for browser localStorage."""

import base64
import gzip
import json
from datetime import datetime

from app.config import APP_TIMEZONE
from app.schemas import Article, TrendReport

STORAGE_KEY = "tech_news_daily_v4"


def today_key() -> str:
    return datetime.now(APP_TIMEZONE).date().isoformat()


def _article_json(article: Article | dict) -> dict:
    if isinstance(article, Article):
        return article.model_dump(mode="json")
    return article


def encode_daily_result(result: dict, day: str | None = None) -> str:
    """Serialize and losslessly compress the complete workflow result."""
    trend = result.get("trend_report")
    payload = {
        "version": 4,
        "day": day or today_key(),
        "summary": result.get("summary", ""),
        "trend_report": trend.model_dump(mode="json") if isinstance(trend, TrendReport) else trend,
        "articles": [_article_json(article) for article in result.get("articles", [])],
        "validated_articles": [_article_json(article) for article in result.get("validated_articles", [])],
        "tech_articles": [_article_json(article) for article in result.get("tech_articles", [])],
        "searched_feeds": result.get("searched_feeds", []),
        "research_rounds": result.get("research_rounds", 0),
        "research_notes": result.get("research_notes", []),
        "research_decision": result.get("research_decision", ""),
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(gzip.compress(raw, mtime=0)).decode("ascii")


def decode_daily_result(value: str | None, day: str | None = None) -> dict | None:
    """Restore a valid full result for today from browser localStorage."""
    if not value:
        return None
    try:
        compressed = base64.b64decode(value, altchars=b"-_", validate=True)
        payload = json.loads(gzip.decompress(compressed).decode("utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("version") != 4
            or payload.get("day") != (day or today_key())
        ):
            return None
        for field in ("articles", "validated_articles", "tech_articles"):
            payload[field] = [Article.model_validate(item) for item in payload.get(field, [])]
        trend = payload.get("trend_report")
        payload["trend_report"] = TrendReport.model_validate(trend) if trend else None
        return payload
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, OSError):
        return None
