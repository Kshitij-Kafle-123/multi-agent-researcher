"""Shared Groq chat-model construction."""

from app.config import GROQ_MODEL


def create_chat_model(*, temperature: float, timeout: int):
    from langchain_groq import ChatGroq

    return ChatGroq(model=GROQ_MODEL, temperature=temperature, max_retries=0, timeout=timeout)
