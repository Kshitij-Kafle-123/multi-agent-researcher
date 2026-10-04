import logging

from app.schemas import Article, ValidationResult
from app.utils.scoring import credibility

logger = logging.getLogger(__name__)


def validate_articles(articles: list[Article]) -> dict[str, list[Article]]:
    validated: list[Article] = []
    for article in articles:
        score, reasons = credibility(article)
        validated.append(article.model_copy(update={
            "credibility_score": score,
            "credibility_reason": " ".join(reasons),
        }))
    logger.info("Validated %d articles", len(validated))
    return {"validated_articles": validated}
