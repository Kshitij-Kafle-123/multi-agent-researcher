from collections import Counter

from app.schemas import KnowledgeItem, TrendReport


def analyze_trends(knowledge: list[KnowledgeItem]) -> dict[str, TrendReport]:
    companies = Counter(name for item in knowledge for name in item.companies)
    technologies = Counter(name for item in knowledge for name in item.technologies)
    frameworks = Counter(name for item in knowledge for name in item.frameworks)
    report = TrendReport(
        most_mentioned_companies=companies.most_common(8),
        most_mentioned_technologies=technologies.most_common(8),
        most_discussed_frameworks=frameworks.most_common(8),
        article_count=len(knowledge),
    )
    return {"trend_report": report}
