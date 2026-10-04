import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import REQUEST_TIMEOUT_SECONDS
from app.schemas import Article

logger = logging.getLogger(__name__)


def enrich_article(article: Article) -> Article:
    """Fetch and extract article text, retaining RSS text if scraping fails."""
    try:
        from newspaper import Article as NewspaperArticle

        parser = NewspaperArticle(str(article.url))
        parser.download()
        parser.parse()
        if parser.text and len(parser.text) > len(article.content):
            return article.model_copy(update={
                "content": parser.text[:30000],
                "author": article.author or (parser.authors[0] if parser.authors else None),
                "published_at": article.published_at or parser.publish_date,
            })
    except Exception as exc:
        logger.debug("newspaper4k extraction failed for %s: %s", article.url, exc)
    try:
        response = requests.get(str(article.url), timeout=REQUEST_TIMEOUT_SECONDS,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; NewsResearchBot/1.0)"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "nav", "footer", "header", "aside"]):
            node.decompose()
        container = soup.find("article") or soup.body or soup
        text = " ".join(p.get_text(" ", strip=True) for p in container.find_all(["p", "h2", "h3"]))
        if text:
            return article.model_copy(update={"content": text[:30000]})
    except Exception as exc:
        logger.debug("BeautifulSoup extraction failed for %s: %s", article.url, exc)
    return article


def source_domain(article: Article) -> str:
    return urlparse(str(article.url)).netloc.lower().removeprefix("www.")
