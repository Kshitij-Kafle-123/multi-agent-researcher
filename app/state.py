from typing import TypedDict

from app.schemas import Article, KnowledgeItem, TrendReport


class NewsState(TypedDict, total=False):
    articles: list[Article]
    validated_articles: list[Article]
    knowledge: list[KnowledgeItem]
    tech_articles: list[Article]
    summary: str
    trend_report: TrendReport
