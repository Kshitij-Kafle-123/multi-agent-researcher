import logging

from app.graph import build_graph
from app.state import NewsState

logger = logging.getLogger(__name__)


def main() -> None:
    workflow = build_graph()
    initial_state: NewsState = {
        "articles": [], "validated_articles": [], "knowledge": [],
        "tech_articles": [], "summary": "", "trend_report": None,
    }
    try:
        result = workflow.invoke(initial_state)
    except Exception:
        logger.exception("News workflow failed")
        raise
    print(result.get("summary") or "# Daily Tech Summary\n\nNo summary was generated.")
    report = result.get("trend_report")
    if report:
        print(f"\n\nCollected {len(result.get('articles', []))} articles; {len(result.get('tech_articles', []))} classified as technology news.")


if __name__ == "__main__":
    main()
