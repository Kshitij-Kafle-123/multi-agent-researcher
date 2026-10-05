import logging

from app.memory.short_term import new_news_state
from app.workflows.research_workflow import build_research_workflow

logger = logging.getLogger(__name__)


def main() -> None:
    workflow = build_research_workflow()
    try:
        result = workflow.invoke(new_news_state())
    except Exception:
        logger.exception("News workflow failed")
        raise
    print(result.get("summary") or "# Daily Tech Summary\n\nNo summary was generated.")
    report = result.get("trend_report")
    if report:
        print(f"\n\nCollected {len(result.get('articles', []))} articles; {len(result.get('tech_articles', []))} classified as technology news.")


if __name__ == "__main__":
    main()
