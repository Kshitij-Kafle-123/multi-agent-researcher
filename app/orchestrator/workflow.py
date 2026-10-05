from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.agents.autonomous_research_agent import research_node
from app.orchestrator.executor import (
    fact_check_node,
    knowledge_node,
    summary_node,
    tech_filter_node,
    trend_node,
    validate_node,
)
from app.state import NewsState


def build_graph(extra_nodes: dict[str, Callable[[NewsState], dict]] | None = None):
    """Build the ordered workflow. Extra nodes may be inserted between named stages.

    Each extension maps an existing stage name (or ``END``) to a node callable;
    insertions keyed to a stage run immediately after that built-in stage, before
    the next stage. Additional extension nodes are chained in mapping order.
    """
    stages: list[tuple[str, Callable[[NewsState], dict]]] = [
        ("validation", validate_node),
        ("fact_check", fact_check_node),
        ("knowledge", knowledge_node),
        ("tech_filter", tech_filter_node),
        ("trend_analysis", trend_node),
        ("summary", summary_node),
    ]
    builder = StateGraph(NewsState)
    builder.add_node("research", research_node)
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
    builder.add_edge(START, "research")
    builder.add_edge("research", route[0])
    for current, following in zip(route, route[1:]):
        builder.add_edge(current, following)
    builder.add_edge(route[-1], END)
    return builder.compile()
