import logging

import streamlit as st

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.graph import build_graph
from app.state import NewsState

logger = logging.getLogger(__name__)


@st.cache_resource
def _workflow():
    return build_graph()


def _run_news() -> dict:
    initial_state: NewsState = {
        "articles": [],
        "validated_articles": [],
        "knowledge": [],
        "tech_articles": [],
        "summary": "",
        "trend_report": None,
    }
    return _workflow().invoke(initial_state)


st.set_page_config(page_title="Tech News Intelligence", page_icon="🗞️", layout="wide")
st.title("🗞️ Tech News Intelligence")
st.caption("This week’s technology stories from BBC News Technology, analyzed by the news agent workflow.")
if GROQ_API_KEY:
    st.caption(f"AI summaries: Groq · {GROQ_MODEL}")
else:
    st.warning("GROQ_API_KEY is missing. Add it to the project’s .env file and restart Streamlit to generate AI summaries.")

if st.button("Fetch and analyze this week’s news", type="primary"):
    try:
        with st.spinner("Loading the BBC feed, scraping articles, and preparing the summary…"):
            st.session_state["news_result"] = _run_news()
            st.session_state.pop("news_error", None)
    except Exception as exc:
        logger.exception("Web UI news workflow failed")
        st.session_state["news_error"] = str(exc)

if error := st.session_state.get("news_error"):
    st.error(f"The news workflow failed: {error}")

result = st.session_state.get("news_result")
if result:
    articles = result.get("tech_articles", [])
    total = len(result.get("articles", []))
    first, second, third = st.columns(3)
    first.metric("Articles collected", total)
    second.metric("Technology stories", len(articles))
    third.metric("Sources", "BBC News Technology")

    st.subheader("Daily Tech Summary")
    st.markdown(result.get("summary") or "No summary was generated.")

    report = result.get("trend_report")
    if report:
        with st.expander("Trends"):
            left, middle, right = st.columns(3)
            left.markdown("**Companies**")
            left.write(report.most_mentioned_companies or "No repeated mentions")
            middle.markdown("**Technologies**")
            middle.write(report.most_mentioned_technologies or "No repeated mentions")
            right.markdown("**Frameworks**")
            right.write(report.most_discussed_frameworks or "No repeated mentions")

    with st.expander(f"Article assessments ({len(articles)})"):
        if not articles:
            st.info("No technology stories were found for this week.")
        for article in articles:
            st.markdown(f"### [{article.title}]({article.url})")
            st.caption(f"{article.source} · {article.published_at or 'Publication date unavailable'}")
            st.write(f"Credibility: **{article.credibility_score}/100** · Truth estimate: **{article.truth_label} ({article.truth_score}/100)** · Confidence: **{article.confidence}/100**")
            if article.ai_summary:
                st.write(article.ai_summary)
            if article.credibility_reason:
                st.write(article.credibility_reason)
            if article.truth_reason:
                st.caption(article.truth_reason)
            st.divider()
else:
    st.info("Click the button to fetch and analyze current-week articles. It may take a minute while article pages are scraped.")
