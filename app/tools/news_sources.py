"""RSS, Google Search, and article-page collection capabilities."""

import logging
from urllib.parse import parse_qs, quote_plus, urlparse

import certifi
import requests
from bs4 import BeautifulSoup

from app.schemas import Article
from app.utils.rss_loader import load_rss_articles
from app.utils.scraper import enrich_article

logger = logging.getLogger(__name__)


def load_feed(feed_url: str) -> list[Article]:
    return load_rss_articles([feed_url])


def enrich_articles(articles: list[Article]) -> list[Article]:
    return [enrich_article(article) for article in articles]


def google_search_articles(query: str, limit: int = 8) -> list[Article]:
    """Scrape Google result links, then extract their article pages with BeautifulSoup fallback."""
    response = requests.get(
        "https://www.google.com/search?q=" + quote_plus(query),
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TechNewsResearch/1.0)"},
        verify=certifi.where(),
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[Article] = []
    seen: set[str] = set()
    for link in soup.select("a"):
        href = link.get("href", "")
        if href.startswith("/url?"):
            href = parse_qs(urlparse(href).query).get("q", [""])[0]
        parsed = urlparse(href)
        heading = link.find(["h3"])
        title = heading.get_text(" ", strip=True) if heading else ""
        if parsed.scheme not in {"http", "https"} or not title or parsed.netloc.endswith("google.com"):
            continue
        if href in seen:
            continue
        seen.add(href)
        candidates.append(Article(title=title, url=href, source=parsed.netloc.removeprefix("www.")))
        if len(candidates) >= limit:
            break
    enriched = [enrich_article(article) for article in candidates]
    logger.info("Google search yielded %d scraped articles", len(enriched))
    return enriched
