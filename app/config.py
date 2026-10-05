import logging
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _setting(name: str, default: str = "") -> str:
    """Read local environment values or Streamlit deployment secrets."""
    value = os.getenv(name)
    if value is not None:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
]
GROQ_API_KEY = _setting("GROQ_API_KEY")
GROQ_MODEL = _setting("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_ARTICLES_PER_FEED = int(_setting("MAX_ARTICLES_PER_FEED", "12"))
REQUEST_TIMEOUT_SECONDS = int(_setting("REQUEST_TIMEOUT_SECONDS", "12"))
MAX_RESEARCH_ROUNDS = max(1, int(_setting("MAX_RESEARCH_ROUNDS", "3")))
APP_TIMEZONE = ZoneInfo(_setting("APP_TIMEZONE", "Asia/Kathmandu"))
logging.basicConfig(
    level=getattr(logging, _setting("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
