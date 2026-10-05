"""Tool-using technology research agent and workflow adapter."""

import json
import logging
from datetime import datetime, time, timedelta

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.agents.instruction_loader import load_agent_instructions
from app.config import A2A_RESEARCH_AGENT_URL, GROQ_API_KEY, RSS_FEEDS
from app.models.llm import create_chat_model
from app.schemas import Article
from app.state import NewsState
from app.tools.news_sources import google_search_articles, load_rss_articles
from app.utils.deduplicator import deduplicate

logger = logging.getLogger(__name__)


@tool
def search_rss_feeds(query: str = "") -> str:
    """Read configured technology-news RSS feeds and return article records as JSON."""
    del query  # The feed entries are supplied as evidence; the agent selects relevant ones.
    records = [article.model_dump(mode="json") for article in load_rss_articles(RSS_FEEDS)]
    return json.dumps(records, ensure_ascii=False)


@tool
def search_google_news(query: str) -> str:
    """Search Google for technology news and return scraped article records as JSON."""
    records = [article.model_dump(mode="json") for article in google_search_articles(query)]
    return json.dumps(records, ensure_ascii=False)


class ResearchAgent:
    """Declarative agent configuration: identity, model, instructions and tools."""

    name = "research_agent"
    description = "Finds current technology news from RSS feeds and Google Search."
    tools = [search_rss_feeds, search_google_news]

    def __init__(self):
        self.instructions = load_agent_instructions("researcher.md")

    def invoke(self, request: str) -> list[Article]:
        if not GROQ_API_KEY:
            # Preserve a useful local mode when model credentials are absent.
            return _local_research()
        agent = create_react_agent(create_chat_model(temperature=0, timeout=45), self.tools)
        response = agent.invoke({
            "messages": [
                ("system", self.instructions),
                ("user", request + " Return a JSON array of article objects using the tool results."),
            ]
        })
        content = str(response["messages"][-1].content)
        try:
            data = json.loads(content.removeprefix("```json").removesuffix("```").strip())
            return [Article.model_validate(item) for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Research agent returned invalid article JSON")
            return []


research_agent = ResearchAgent()


def _current_week(articles: list[Article]) -> list[Article]:
    now = datetime.now().astimezone()
    start_date = now.date() - timedelta(days=now.weekday())
    start = datetime.combine(start_date, time.min, tzinfo=now.tzinfo)
    return [
        article for article in articles
        if article.published_at is not None
        and start <= article.published_at.astimezone(now.tzinfo) <= now
    ]


def _local_research() -> list[Article]:
    """Fallback for installations without Groq credentials."""
    from app.tools.news_sources import enrich_articles

    articles = deduplicate(_current_week(load_rss_articles(RSS_FEEDS)))
    return enrich_articles(articles[:60])


def research_node(state: NewsState) -> dict[str, object]:
    request = "Find relevant technology news published this week. Search RSS feeds and Google when useful."
    if A2A_RESEARCH_AGENT_URL:
        from app.agents.a2a_client import request_research

        articles = request_research(request)
    else:
        articles = research_agent.invoke(request)
    return {
        "articles": deduplicate(_current_week(articles)),
        "research_notes": [f"research_agent collected {len(articles)} candidate articles."],
    }
