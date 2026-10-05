"""RSS and article-page collection capability."""

from app.schemas import Article
from app.utils.rss_loader import load_rss_articles
from app.utils.scraper import enrich_article


def load_feed(feed_url: str) -> list[Article]:
    return load_rss_articles([feed_url])


def enrich_articles(articles: list[Article]) -> list[Article]:
    return [enrich_article(article) for article in articles]
