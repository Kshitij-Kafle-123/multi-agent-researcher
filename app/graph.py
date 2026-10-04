from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.agents.fact_agent import fact_check_articles
from app.agents.knowledge_agent import build_knowledge
from app.agents.research_agent import research
from app.agents.summary_agent import summarize
from app.agents.tech_filter_agent import filter_technology
from app.agents.trend_agent import analyze_trends
from app.agents.validation_agent import validate_articles
from app.state import NewsState


def _validation_node(state: NewsState) -> dict:
    return validate_articles(state.get("articles", []))


def _fact_check_node(state: NewsState) -> dict:
    return {"validated_articles": fact_check_articles(state.get("validated_articles", []))}


def _knowledge_node(state: NewsState) -> dict:
    return {"knowledge": build_knowledge(state.get("validated_articles", []))}


def _summary_node(state: NewsState) -> dict:
    return summarize(state.get("tech_articles", []), state.get("trend_report"))


def build_graph(extra_nodes: dict[str, Callable[[NewsState], dict]] | None = None):
    """Build the ordered workflow. Extra nodes may be inserted between named stages.

    Each extension maps an existing stage name (or ``END``) to a node callable;
    insertions keyed to a stage run immediately after that built-in stage, before
    the next stage. Additional extension nodes are chained in mapping order.
    """
    stages: list[tuple[str, Callable[[NewsState], dict]]] = [
        ("research", lambda state: research()),
        ("validation", _validation_node),
        ("fact_check", _fact_check_node),
        ("knowledge", _knowledge_node),
        ("tech_filter", lambda state: filter_technology(state.get("validated_articles", []))),
        ("trend_analysis", lambda state: analyze_trends(state.get("knowledge", []))),
        ("summary", _summary_node),
    ]
    builder = StateGraph(NewsState)
    for name, node in stages:
        builder.add_node(name, node)
    insertions: dict[str, list[str]] = {}
    for index, (name, node) in enumerate((extra_nodes or {}).items()):
        node_name = f"extension_{index}_{name}"
        builder.add_node(node_name, node)
        insertions.setdefault(name, []).append(node_name)

    route: list[str] = []
    for name, _ in stages:
        route.append(name)
        route.extend(insertions.get(name, []))
    route.extend(insertions.get(END, []))
    builder.add_edge(START, route[0])
    for current, following in zip(route, route[1:]):
        builder.add_edge(current, following)
    builder.add_edge(route[-1], END)
    return builder.compile()
