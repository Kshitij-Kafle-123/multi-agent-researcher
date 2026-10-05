"""Execute deterministic analysis stages over the shared news state."""

from app.agents.fact_agent import fact_check_articles
from app.agents.knowledge_agent import build_knowledge
from app.agents.summary_agent import summarize
from app.agents.tech_filter_agent import filter_technology
from app.agents.trend_agent import analyze_trends
from app.agents.validation_agent import validate_articles
from app.state import NewsState


def validate_node(state: NewsState) -> dict:
    return validate_articles(state.get("articles", []))


def fact_check_node(state: NewsState) -> dict:
    return {"validated_articles": fact_check_articles(state.get("validated_articles", []))}


def knowledge_node(state: NewsState) -> dict:
    return {"knowledge": build_knowledge(state.get("validated_articles", []))}


def tech_filter_node(state: NewsState) -> dict:
    return filter_technology(state.get("validated_articles", []))


def trend_node(state: NewsState) -> dict:
    return analyze_trends(state.get("knowledge", []))


def summary_node(state: NewsState) -> dict:
    return summarize(state.get("tech_articles", []), state.get("trend_report"))
