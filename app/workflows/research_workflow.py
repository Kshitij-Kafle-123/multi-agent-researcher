"""Public entry point for the technology-news research workflow."""

from app.orchestrator.workflow import build_graph


def build_research_workflow():
    return build_graph()
