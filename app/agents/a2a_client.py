"""Synchronous workflow adapter for the A2A research agent."""

import asyncio
import json

from app.config import A2A_RESEARCH_AGENT_URL
from app.schemas import Article


async def _request_remote(query: str) -> list[Article]:
    import httpx
    from a2a.client import A2ACardResolver, ClientConfig, create_client
    from a2a.helpers import get_message_text, new_text_message
    from a2a.types import Role, SendMessageRequest

    async with httpx.AsyncClient() as http_client:
        resolver = A2ACardResolver(httpx_client=http_client, base_url=A2A_RESEARCH_AGENT_URL)
        card = await resolver.get_agent_card()
        client = await create_client(agent=card, client_config=ClientConfig(streaming=False))
        try:
            request = SendMessageRequest(message=new_text_message(query, role=Role.ROLE_USER))
            async for item in client.send_message(request):
                envelope = getattr(item, "root", item)
                result = getattr(envelope, "result", envelope)
                text = get_message_text(result)
                if text:
                    payload = json.loads(text)
                    return [Article.model_validate(article) for article in payload]
        finally:
            await client.close()
    return []


def request_research(query: str) -> list[Article]:
    """Call the configured remote A2A agent; return [] when no endpoint is set."""
    if not A2A_RESEARCH_AGENT_URL:
        return []
    return asyncio.run(_request_remote(query))
