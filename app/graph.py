"""Backward-compatible import path for the news workflow graph."""

from app.orchestrator.workflow import build_graph

__all__ = ["build_graph"]
