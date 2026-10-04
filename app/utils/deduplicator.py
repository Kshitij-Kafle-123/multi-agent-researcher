import re
from difflib import SequenceMatcher

from app.schemas import Article


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def deduplicate(articles: list[Article]) -> list[Article]:
    """Keep the first article for each URL or near-identical headline."""
    output: list[Article] = []
    urls: set[str] = set()
    titles: list[str] = []
    for article in articles:
        url = str(article.url).split("?")[0].rstrip("/").lower()
        title = _normalize(article.title)
        if url in urls or any(SequenceMatcher(None, title, existing).ratio() >= 0.9 for existing in titles):
            continue
        urls.add(url)
        titles.append(title)
        output.append(article)
    return output
