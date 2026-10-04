import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import certifi
import feedparser
import requests

from app.config import MAX_ARTICLES_PER_FEED, RSS_FEEDS
from app.schemas import Article

logger = logging.getLogger(__name__)


def _published(entry: object) -> datetime | None:
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if raw:
        try:
            date = parsedate_to_datetime(raw)
            return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date
        except (TypeError, ValueError, OverflowError):
            pass
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    return datetime(*parsed[:6], tzinfo=timezone.utc) if parsed else None


def load_rss_articles(feeds: list[str] | None = None) -> list[Article]:
    articles: list[Article] = []
    for feed_url in feeds or RSS_FEEDS:
        try:
            response = requests.get(
                feed_url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NewsResearchBot/1.0)"},
                verify=certifi.where(),
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            if getattr(feed, "bozo", False):
                logger.warning("Feed parse warning for %s: %s", feed_url, feed.get("bozo_exception"))
            source = feed.feed.get("title", feed_url.split("/")[2])
            for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
                link = entry.get("link")
                title = entry.get("title", "").strip()
                if not link or not title:
                    continue
                summary = entry.get("summary", "")
                articles.append(Article(
                    title=title, url=link, published_at=_published(entry),
                    author=entry.get("author"), content=summary, source=source,
                ))
        except Exception:
            logger.exception("Could not load RSS feed %s", feed_url)
    return articles
