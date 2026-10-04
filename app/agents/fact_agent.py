import logging
import re
from collections import Counter

from app.schemas import Article

logger = logging.getLogger(__name__)
ENTITY_RE = re.compile(r"\b[A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,2}\b")


def fact_check_articles(articles: list[Article]) -> list[Article]:
    """Estimate cross-source support; this is a heuristic, not external fact checking."""
    headline_entities = [set(ENTITY_RE.findall(a.title)) for a in articles]
    results: list[Article] = []
    for index, article in enumerate(articles):
        own = headline_entities[index]
        matches = []
        for other_index, other in enumerate(articles):
            if index == other_index or other.source == article.source:
                continue
            overlap = own.intersection(headline_entities[other_index])
            if overlap:
                matches.append((other, overlap))
        corroborating_sources = {other.source for other, _ in matches}
        score = min(92, 52 + 12 * len(corroborating_sources))
        confidence = min(90, 35 + 15 * len(corroborating_sources))
        reasons = [f"{len(corroborating_sources)} other source(s) had headline entity overlap."]
        if not own:
            score -= 8
            confidence -= 10
            reasons.append("No named entities could be extracted from the headline.")
        if article.credibility_score is not None and article.credibility_score >= 75:
            score += 4
            reasons.append("The source has a high credibility heuristic score.")
        dates = [other.published_at for other, _ in matches if other.published_at and article.published_at]
        if dates:
            close = any(abs((date - article.published_at).total_seconds()) < 72 * 3600 for date in dates)
            reasons.append("Corroborating publication timestamps are close." if close else "Related headlines have differing publication timestamps.")
            if close:
                score += 5
        score, confidence = max(0, min(score, 100)), max(0, min(confidence, 100))
        label = "Likely True" if score >= 80 else "Possibly True" if score >= 65 else "Needs Verification" if score >= 40 else "Likely False"
        results.append(article.model_copy(update={
            "truth_score": score, "confidence": confidence, "truth_label": label,
            "truth_reason": " ".join(reasons),
        }))
    logger.info("Estimated cross-source support for %d articles", len(results))
    return results
