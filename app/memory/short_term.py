"""Per-run working state used by the news workflow."""

from app.state import NewsState


def new_news_state() -> NewsState:
    return {
        "searched_feeds": [],
        "research_rounds": 0,
        "research_notes": [],
        "articles": [],
        "validated_articles": [],
        "knowledge": [],
        "tech_articles": [],
        "summary": "",
        "trend_report": None,
    }
