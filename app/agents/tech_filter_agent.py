from app.schemas import Article

TECH_TERMS = (
    "technology", "tech", "software", "developer", "programming", "ai", "artificial intelligence",
    "llm", "cloud", "cybersecurity", "open source", "mobile", "hardware", "startup", "chip",
    "robot", "data", "app", "internet", "computer", "framework", "api", "google", "microsoft",
    "apple", "meta", "amazon", "nvidia", "python", "security", "machine learning",
)


def filter_technology(articles: list[Article]) -> dict[str, list[Article]]:
    kept = []
    for article in articles:
        text = f"{article.title} {article.content[:2500]}".lower()
        matched = [term for term in TECH_TERMS if term in text]
        if matched:
            kept.append(article.model_copy(update={"is_technology": True, "category": matched[0].title()}))
    return {"tech_articles": kept}
