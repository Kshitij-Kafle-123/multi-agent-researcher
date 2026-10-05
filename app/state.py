from typing import TypedDict

from app.schemas import Article, KnowledgeItem, TrendReport


class NewsState(TypedDict, total=False):
    searched_feeds: list[str]
    research_rounds: int
    research_notes: list[str]
    next_feed: str | None
    research_decision: str
    articles: list[Article]
    validated_articles: list[Article]
    knowledge: list[KnowledgeItem]
    tech_articles: list[Article]
    summary: str
    trend_report: TrendReport
