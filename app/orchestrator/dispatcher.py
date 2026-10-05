"""Routing decisions for the research workflow."""

from app.state import NewsState


def after_research_plan(state: NewsState) -> str:
    return "collect" if state.get("next_feed") else "validation"
