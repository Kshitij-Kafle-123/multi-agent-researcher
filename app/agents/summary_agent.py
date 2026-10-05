import logging
import re
import time

from app.agents.instruction_loader import load_agent_instructions
from app.config import GROQ_API_KEY
from app.models.llm import create_chat_model
from app.schemas import Article, TrendReport

logger = logging.getLogger(__name__)
SENTENCE_END_RE = re.compile(r"[.!?](?=\s|$)")


def _complete_ai_summary(text: str) -> str | None:
    """Keep complete sentences from a Groq response, dropping any trailing fragment."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return None
    ends = [match.end() for match in SENTENCE_END_RE.finditer(cleaned)]
    if not ends:
        return None
    return cleaned[:ends[-1]].strip() or None


def _digest(articles: list[Article], trends: TrendReport | None) -> str:
    lines = [
        "# Daily Tech Summary",
        "",
        f"*Summaries generated with Groq for {sum(bool(article.ai_summary) for article in articles)} of {len(articles)} stories.*",
        "",
        "## Top Headlines",
        "",
    ]
    if not articles:
        lines.append("No technology stories were found in this collection.")
    for article in articles:
        lines.extend([
            f"### [{article.title}]({article.url})",
            f"*{article.source} · {article.published_at or 'Publication date unavailable'}*",
            "",
            article.ai_summary or "Groq did not return a summary for this story.",
            "",
        ])
    if trends:
        lines.extend(["## Trends", ""])
        for name, values in (
            ("Companies", trends.most_mentioned_companies),
            ("Technologies", trends.most_mentioned_technologies),
            ("Frameworks", trends.most_discussed_frameworks),
        ):
            items = ", ".join(f"{label} ({count})" for label, count in values) or "No repeated mentions"
            lines.append(f"- **{name}:** {items}")
    return "\n".join(lines)


def summarize(articles: list[Article], trends: TrendReport | None) -> dict[str, object]:
    if not articles:
        return {"summary": _digest([], trends), "tech_articles": []}
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required to generate news summaries.")

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        model = create_chat_model(temperature=0.2, timeout=60)
        system_message = SystemMessage(content=load_agent_instructions("writer.md"))
    except Exception as exc:
        logger.exception("Could not initialize the Groq summarizer")
        raise RuntimeError("Could not initialize Groq. Check the model and API key configuration.") from exc

    summarized: list[Article] = []
    for article in articles:
        article_text = article.content[:3000].strip() or article.title
        messages = [
            system_message,
            HumanMessage(content=(
                f"Summarize this story in 2 to 4 complete sentences. Do not end mid-sentence. "
                f"Use only this supplied material.\n\nTitle: {article.title}\nSource: {article.source}\n"
                f"Article text:\n{article_text}"
            )),
        ]
        summary = None
        last_error = "Groq returned no complete sentence."
        for attempt in range(3):
            try:
                response = model.invoke(messages)
                summary = _complete_ai_summary(str(response.content))
                if summary:
                    break
                last_error = "Groq returned no complete sentence."
                logger.warning("Groq returned an incomplete summary for '%s'", article.title)
                if attempt < 2:
                    messages.append(HumanMessage(content="Rewrite the summary with complete sentences and a complete final sentence."))
            except Exception as exc:
                last_error = str(exc)
                if "rate limit" not in last_error.lower() and "429" not in last_error:
                    logger.warning("Groq could not summarize '%s': %s", article.title, exc)
                    break
                wait_match = re.search(r"try again in\s+([\d.]+)s", last_error, re.IGNORECASE)
                wait_seconds = float(wait_match.group(1)) + 1 if wait_match else 15
                logger.warning("Groq rate limit for '%s'; retrying in %.1f seconds", article.title, wait_seconds)
                if attempt < 2:
                    time.sleep(wait_seconds)
        if not summary:
            raise RuntimeError(f"Groq failed to create a complete summary for '{article.title}': {last_error}")
        summarized.append(article.model_copy(update={"ai_summary": summary}))

    return {"summary": _digest(summarized, trends), "tech_articles": summarized}
