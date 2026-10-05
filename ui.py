import logging

import extra_streamlit_components as stx
import streamlit as st

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.memory.daily_cookie_cache import (
    COOKIE_NAME,
    cookie_expiration,
    decode_daily_result,
    encode_daily_result,
    today_key,
)
from app.memory.short_term import new_news_state
from app.workflows.research_workflow import build_research_workflow

logger = logging.getLogger(__name__)


@st.cache_resource
def _workflow():
    return build_research_workflow()


def _run_news() -> dict:
    return _workflow().invoke(new_news_state())


@st.fragment
def _cookie_manager():
    return stx.CookieManager(key="daily_news_cookie_manager")


st.set_page_config(page_title="Tech News Intelligence", page_icon="🗞️", layout="wide")
st.title("🗞️ Tech News Intelligence")
st.caption("This week’s technology stories, gathered through a bounded autonomous research loop and analyzed by the news workflow.")
if GROQ_API_KEY:
    st.caption(f"AI summaries: Groq · {GROQ_MODEL}")
else:
    st.warning("GROQ_API_KEY is missing. Add it to .env locally or the platform’s secrets settings before generating the digest.")

cookie_manager = _cookie_manager()
today = today_key()
cached_result = decode_daily_result(cookie_manager.get(COOKIE_NAME), today)
if cached_result:
    st.session_state["news_result"] = cached_result
    st.session_state["news_result_day"] = today
    st.session_state["news_result_cache_version"] = 3
elif (
    st.session_state.get("news_result_day") != today
    or st.session_state.get("news_result_cache_version") != 3
):
    st.session_state.pop("news_result", None)
    st.session_state.pop("news_result_day", None)

already_generated_today = st.session_state.get("news_result_day") == today and st.session_state.get("news_result")
if already_generated_today:
    st.info("Today’s news digest is saved in this browser and will be reused until midnight.")
elif st.button("Fetch and analyze this week’s news", type="primary"):
    try:
        with st.spinner("Choosing news sources, collecting articles, and preparing the summary…"):
            fresh_result = _run_news()
            cookie_value, summary_truncated = encode_daily_result(fresh_result, today)
            cookie_manager.set(
                COOKIE_NAME,
                cookie_value,
                expires_at=cookie_expiration(),
                path="/",
                same_site="lax",
            )
            restored_result = decode_daily_result(cookie_value, today)
            if restored_result is None:
                raise ValueError("The browser could not restore the saved daily digest")
            restored_result["summary_truncated"] = summary_truncated
            st.session_state["news_result"] = restored_result
            st.session_state["news_result_day"] = today
            st.session_state["news_result_cache_version"] = 3
            st.session_state.pop("news_error", None)
    except Exception as exc:
        logger.exception("Web UI news workflow failed")
        st.session_state["news_error"] = str(exc)

if error := st.session_state.get("news_error"):
    st.error(f"The news workflow failed: {error}")

result = st.session_state.get("news_result")
if result:
    articles = result.get("tech_articles", [])
    total = result.get("articles_count", len(result.get("articles", [])))
    technology_count = result.get("tech_article_count", len(articles))
    first, second, third = st.columns(3)
    first.metric("Articles collected", total)
    second.metric("Technology stories", technology_count)
    third.metric("Sources searched", len(result.get("searched_feeds", [])))

    st.subheader("Daily Tech Summary")
    st.markdown(result.get("summary") or "No summary was generated.")
    if result.get("summary_truncated"):
        st.warning("This digest was shortened to fit the browser cookie size limit. The browser will still reuse it for today.")
    if result.get("assessments_saved") is False:
        st.caption("Article assessments were omitted from the cookie to keep the saved digest within browser limits.")

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

    with st.expander("Autonomous research decisions"):
        for note in result.get("research_notes", []):
            st.write(note)
        if result.get("research_decision"):
            st.caption(f"Planner stopped: {result['research_decision']}")

    with st.expander(f"Article assessments ({technology_count})"):
        if not articles:
            if technology_count:
                st.info("Article assessments were not saved in the browser cookie; the daily digest above is available.")
            else:
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
