from datetime import datetime, timezone

from app.schemas import Article

TRUSTED_DOMAINS = ("techcrunch.com", "theverge.com", "arstechnica.com", "nytimes.com", "wired.com", "bbc.co.uk")


def credibility(article: Article, duplicate: bool = False) -> tuple[int, list[str]]:
    score, reasons = 55, []
    domain = str(article.url).split("/")[2].lower().removeprefix("www.")
    if any(domain == trusted or domain.endswith("." + trusted) for trusted in TRUSTED_DOMAINS):
        score += 25
        reasons.append("Established publication in the configured technology news sources.")
    else:
        reasons.append("Source is not in the configured trusted-source list.")
    length = len(article.content.strip())
    if length >= 800:
        score += 10
        reasons.append("Article contains substantial extracted text.")
    elif length < 180:
        score -= 12
        reasons.append("Article text is short or may only be a feed excerpt.")
    title = article.title.lower()
    clickbait = ("you won't believe", "shocking", "must see", "what happens next", "secret they", "!!!")
    if any(term in title for term in clickbait):
        score -= 20
        reasons.append("Title contains common clickbait wording or punctuation.")
    if article.published_at:
        age_days = (datetime.now(timezone.utc) - article.published_at.astimezone(timezone.utc)).days
        if -1 <= age_days <= 14:
            score += 8
            reasons.append("Publication date is recent.")
        elif age_days > 180:
            score -= 15
            reasons.append("Publication date is old.")
    else:
        score -= 8
        reasons.append("Publication date is unavailable.")
    if duplicate:
        score -= 30
        reasons.append("A duplicate headline or URL was detected.")
    return max(0, min(100, score)), reasons
