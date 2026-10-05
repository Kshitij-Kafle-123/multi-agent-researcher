"""A2A server exposing the autonomous technology research agent."""

import asyncio
import json

import uvicorn
from a2a.helpers import get_message_text, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, Role
from starlette.applications import Starlette

from app.agents.autonomous_research_agent import research_agent


class ResearchAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Answer each A2A request with a JSON array of researched article records."""
        query = get_message_text(context.message)
        articles = await asyncio.to_thread(research_agent.invoke, query)
        payload = json.dumps([article.model_dump(mode="json") for article in articles], ensure_ascii=False)
        await event_queue.enqueue_event(new_text_message(payload, role=Role.ROLE_AGENT))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Research requests cannot be cancelled once scraping starts.")


def create_app() -> Starlette:
    url = "http://127.0.0.1:8765"
    card = AgentCard(
        name=research_agent.name,
        description=research_agent.description,
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[AgentInterface(protocol_binding="JSONRPC", url=url, protocol_version="1.0")],
        skills=[AgentSkill(
            id="technology-news-research",
            name="Technology news research",
            description="Finds and scrapes technology news using RSS and Google Search.",
            input_modes=["text/plain"],
            output_modes=["text/plain"],
            tags=["technology", "news", "research"],
        )],
    )
    handler = DefaultRequestHandler(
        agent_executor=ResearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    return Starlette(routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, "/")])


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8765)
