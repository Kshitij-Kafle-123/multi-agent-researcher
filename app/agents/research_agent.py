import logging
from datetime import datetime, time
from datetime import timedelta

from app.schemas import Article
from app.utils.deduplicator import deduplicate
from app.utils.rss_loader import load_rss_articles
from app.utils.scraper import enrich_article

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


def research() -> dict[str, list[Article]]:
    candidates = deduplicate(_current_week_articles(load_rss_articles()))
    # Scraping is deliberately bounded so one run remains useful when feeds are busy.
    articles = [enrich_article(article) for article in candidates[:60]]
    logger.info("Research collected %d unique articles from the current week", len(articles))
    return {"articles": articles}
