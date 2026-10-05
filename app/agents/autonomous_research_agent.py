"""Bounded planner that chooses which configured news feed to research next."""

import json
import logging

from app.config import GROQ_API_KEY, MAX_RESEARCH_ROUNDS, RSS_FEEDS
from app.agents.instruction_loader import load_agent_instructions
from app.models.llm import create_chat_model
from app.state import NewsState

logger = logging.getLogger(__name__)


def plan_research(state: NewsState) -> dict[str, object]:
    searched = state.get("searched_feeds", [])
    remaining = [feed for feed in RSS_FEEDS if feed not in searched]
    rounds = state.get("research_rounds", 0)
    articles = state.get("articles", [])
    if not remaining or rounds >= MAX_RESEARCH_ROUNDS:
        return {"next_feed": None, "research_decision": "finish"}

    # Let the model decide whether more collection is useful and which approved
    # feed to use. It cannot introduce URLs or invoke arbitrary tools.
    if GROQ_API_KEY:
        try:
            prompt = {
                "agent_instructions": load_agent_instructions("planner.md"),
                "article_count": len(articles),
                "sources_already_searched": searched,
                "available_feeds": remaining,
                "limits": f"At most {MAX_RESEARCH_ROUNDS} total research rounds. Select a feed exactly from available_feeds or choose finish.",
                "response_format": '{"action":"research|finish","feed":"exact URL or null","reason":"short explanation"}',
            }
            response = create_chat_model(temperature=0, timeout=20).invoke(
                "Choose the next research step. Return only JSON.\n" + json.dumps(prompt)
            )
            raw = str(response.content).strip().removeprefix("```json").removesuffix("```").strip()
            decision = json.loads(raw)
            feed = decision.get("feed")
            if decision.get("action") == "research" and feed in remaining:
                logger.info("Research planner selected %s: %s", feed, decision.get("reason", ""))
                return {"next_feed": feed, "research_decision": str(decision.get("reason", "continue research"))}
            if decision.get("action") == "finish":
                return {"next_feed": None, "research_decision": str(decision.get("reason", "research complete"))}
            logger.warning("Research planner returned an invalid choice; using bounded fallback")
        except Exception:
            logger.exception("Research planning failed; using bounded fallback")

    # A deterministic fallback keeps the workflow useful without model access.
    feed = remaining[0]
    return {"next_feed": feed, "research_decision": "Continue with an unsearched configured source."}


def collect_from_selected_feed(state: NewsState) -> dict[str, object]:
    from app.agents.research_agent import research

    feed = state.get("next_feed")
    if not feed or feed not in RSS_FEEDS:
        return {"next_feed": None}
    found = research(feed).get("articles", [])
    existing = state.get("articles", [])
    known_urls = {str(article.url) for article in existing}
    combined = existing + [article for article in found if str(article.url) not in known_urls]
    searched = state.get("searched_feeds", [])
    note = f"{feed}: collected {len(found)} articles, {len(combined) - len(existing)} new after deduplication."
    logger.info(note)
    return {
        "articles": combined,
        "searched_feeds": searched + [feed],
        "research_rounds": state.get("research_rounds", 0) + 1,
        "research_notes": state.get("research_notes", []) + [note],
    }
