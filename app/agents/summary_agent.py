import logging
import re
import time

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas import Article, TrendReport

logger = logging.getLogger(__name__)


def _fallback_summary(articles: list[Article], trends: TrendReport | None) -> str:
    groups = {
        "Top Headlines": articles[:8],
        "Important Innovations": [a for a in articles if any(t in (a.title + a.content).lower() for t in ("launch", "announce", "new", "breakthrough"))][:5],
        "Open Source News": [a for a in articles if "open source" in (a.title + a.content).lower() or "github" in (a.title + a.content).lower()][:5],
        "AI News": [a for a in articles if any(t in (a.title + a.content).lower() for t in (" ai ", "artificial intelligence", "llm", "model"))][:5],
        "Cloud News": [a for a in articles if "cloud" in (a.title + a.content).lower()][:5],
        "Developer News": [a for a in articles if any(t in (a.title + a.content).lower() for t in ("developer", "programming", "software"))][:5],
        "Security News": [a for a in articles if any(t in (a.title + a.content).lower() for t in ("security", "hack", "breach"))][:5],
        "Startup News": [a for a in articles if any(t in (a.title + a.content).lower() for t in ("startup", "funding", "raises"))][:5],
    }
    lines = ["# Daily Tech Summary", "", "*Generated from collected news; headlines link to source articles.*", ""]
    for heading, group in groups.items():
        lines.extend([f"## {heading}", ""])
        if not group:
            lines.extend(["No matching stories in this collection.", ""])
            continue
        for article in group:
            lines.append(f"- [{article.title}]({article.url}) — {article.source}.")
        lines.append("")
    if trends:
        lines.extend(["## Trends", ""])
        for name, values in (("Companies", trends.most_mentioned_companies), ("Technologies", trends.most_mentioned_technologies), ("Frameworks", trends.most_discussed_frameworks)):
            lines.append(f"- **{name}:** " + (", ".join(f"{label} ({count})" for label, count in values) or "No repeated mentions"))
    return "\n".join(lines)


def _digest(articles: list[Article], trends: TrendReport | None) -> str:
    summarized_count = sum(bool(article.ai_summary) for article in articles)
    intro = f"*AI summaries generated for {summarized_count} of {len(articles)} stories; article excerpts fill any gaps.*"
    lines = ["# Daily Tech Summary", "", intro, "", "## Top Headlines", ""]
    if not articles:
        lines.append("No technology stories were found in this collection.")
    for article in articles:
        lines.extend([
            f"### [{article.title}]({article.url})",
            f"*{article.source} · {article.published_at or 'Publication date unavailable'}*",
            "",
            article.ai_summary or article.content[:350] or "No article text was available to summarize.",
            "",
        ])
    if trends:
        lines.extend(["## Trends", ""])
        for name, values in (("Companies", trends.most_mentioned_companies), ("Technologies", trends.most_mentioned_technologies), ("Frameworks", trends.most_discussed_frameworks)):
            items = ", ".join(f"{label} ({count})" for label, count in values) or "No repeated mentions"
            lines.append(f"- **{name}:** {items}")
    return "\n".join(lines)


def summarize(articles: list[Article], trends: TrendReport | None) -> dict[str, object]:
    if not GROQ_API_KEY or not articles:
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is unset; using article excerpts instead of AI summaries")
        return {"summary": _digest(articles, trends), "tech_articles": articles}
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        model = ChatGroq(model=GROQ_MODEL, temperature=0.2, max_retries=0, timeout=60)
        summarized = []
        for article in articles:
            messages = [
                SystemMessage(content="Summarize this news article in 2 to 4 concise sentences. Use only the supplied title and article text. Do not infer unsupported facts. State the main development and its significance to technology readers."),
                HumanMessage(content=f"Title: {article.title}\nSource: {article.source}\nArticle text:\n{article.content[:3000] or article.title}"),
            ]
            summary = None
            for attempt in range(3):
                try:
                    response = model.invoke(messages)
                    summary = str(response.content).strip()
                    break
                except Exception as exc:
                    # Groq includes the time to wait in its rate-limit response.
                    if "rate limit" not in str(exc).lower() and "429" not in str(exc):
                        logger.warning("Groq could not summarize '%s': %s", article.title, exc)
                        break
                    wait_match = re.search(r"try again in\s+([\d.]+)s", str(exc), re.IGNORECASE)
                    wait_seconds = float(wait_match.group(1)) + 1 if wait_match else 15
                    logger.warning("Groq rate limit for '%s'; retrying in %.1f seconds", article.title, wait_seconds)
                    if attempt < 2:
                        time.sleep(wait_seconds)
            summarized.append(article.model_copy(update={"ai_summary": summary or None}))
        return {"summary": _digest(summarized, trends), "tech_articles": summarized}
    except Exception:
        logger.exception("Groq summarization setup failed; using article excerpts instead")
        return {"summary": _digest(articles, trends), "tech_articles": articles}
