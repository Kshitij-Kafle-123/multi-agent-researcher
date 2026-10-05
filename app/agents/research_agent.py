import logging
from datetime import datetime, time
from datetime import timedelta

from app.config import RSS_FEEDS
from app.schemas import Article
from app.utils.deduplicator import deduplicate
from app.tools.news_sources import enrich_articles, load_feed

logger = logging.getLogger(__name__)


def _current_week_articles(articles: list[Article]) -> list[Article]:
    """Keep articles published since Monday 00:00 in the machine's local timezone."""
    now = datetime.now().astimezone()
    week_start_date = now.date() - timedelta(days=now.weekday())
    week_start = datetime.combine(week_start_date, time.min, tzinfo=now.tzinfo)
    current_week = []
    for article in articles:
        if article.published_at is None:
            logger.debug("Skipping article without publication date: %s", article.title)
            continue
        published = article.published_at.astimezone(now.tzinfo)
        if week_start <= published <= now:
            current_week.append(article)
    return current_week


def research(feed_url: str | None = None) -> dict[str, list[Article]]:
    feeds = [feed_url] if feed_url else RSS_FEEDS
    raw_articles = [article for feed in feeds for article in load_feed(feed)]
    candidates = deduplicate(_current_week_articles(raw_articles))
    # Scraping is deliberately bounded so one run remains useful when feeds are busy.
    articles = enrich_articles(candidates[:60])
    logger.info("Research collected %d unique articles from the current week", len(articles))
    return {"articles": articles}
