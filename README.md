# Multi-Agent AI News Intelligence System

A Python 3.12 demonstration that collects technology headlines from RSS feeds, extracts article text, applies transparent quality and cross-source support heuristics, builds structured knowledge, filters technology stories, reports trends, and prints a Markdown digest. LangGraph runs each responsibility as a distinct stage.

## Installation

Use Python 3.12, create a virtual environment, and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`. Set `GROQ_API_KEY` to enable the tool-using research agent and Groq summaries. The default model is `openai/gpt-oss-120b`; change `GROQ_MODEL` if you prefer another model enabled for your Groq account. Streamlit deployments can provide `GROQ_API_KEY` and `GROQ_MODEL` through `st.secrets`. Without a Groq key, collection falls back to the configured RSS feeds. News collection uses public RSS feeds and does not require a news API key.

## Run

Launch the web UI:

```bash
streamlit run ui.py
```

Open the local URL Streamlit prints, then select **Fetch and analyze this week’s news**. The page shows the generated digest, trends, and article assessments.

The UI saves the complete compressed workflow result in browser `localStorage`, including the digest, trends, collected articles, and assessments. It restores that result after refresh and prevents another generation in the same browser until midnight in `APP_TIMEZONE` (defaults to `Asia/Kathmandu`). Clearing site data or using another browser starts a separate daily cache. Browser storage has a per-site quota, but the app no longer truncates content to meet a cookie-size cap.

Or run the workflow in the terminal:

```bash
python main.py
```

The program prints its digest and a collection count. It keeps articles published since Monday at 00:00 in the machine's local timezone, then scrapes each article page. Feed, scraping, and model errors are logged; failed page extraction falls back to the text included in the RSS entry. `MAX_ARTICLES_PER_FEED`, `REQUEST_TIMEOUT_SECONDS`, and `LOG_LEVEL` can be adjusted in `.env`.

## Architecture

- `app/agents/` contains the tool-using research agent, optional A2A server/client adapters, and focused analysis agents.
- `app/prompts/` holds agent role prompts. The researcher and writer prompts are loaded into LLM calls.
- `app/orchestrator/` routes workflow stages and executes the analysis nodes; `app/workflows/` exposes the runnable research workflow.
- `app/tools/` wraps RSS loading and article enrichment; `app/utils/` provides feed parsing, scraping, deduplication, and scoring helpers.
- `app/memory/short_term.py` creates per-run state. `app/state.py` defines its type and `app/schemas.py` defines Pydantic data models.
- `app/models/llm.py` centralizes chat model setup. `main.py` and `ui.py` invoke the workflow.

This project uses in-memory workflow state and public RSS/article pages, so it does not include persistent databases, vector storage, or a scheduled background worker.

### A2A research agent

The research agent is available as an A2A JSON-RPC service. Start it in a separate terminal with `python -m app.agents.a2a_server`; its Agent Card is served at `http://127.0.0.1:8765/.well-known/agent-card.json`. The workflow calls this service over A2A when `A2A_RESEARCH_AGENT_URL=http://127.0.0.1:8765` is set. If the URL is unset, the workflow invokes the same agent locally. A2A follows the official Python SDK's Agent Card, executor, task/message, and JSON-RPC route model.

## LangGraph flow

```text
START → research_agent (RSS and Google Search scraper tools)
      → validation → fact_check → knowledge → tech_filter
      → trend_analysis → summary → END
```

The research agent receives both RSS and Google Search scraping tools and decides which to use for the request. When configured, the workflow and research agent communicate over A2A JSON-RPC; the research service advertises its capabilities with an Agent Card.

Add a node with `build_graph(extra_nodes={"validation": my_node})` to insert it immediately after the named stage. The built-in agents do not need to be rewritten to extend the graph.

Credibility and truth values are explainable heuristics based on source identity, available article text and dates, and overlap between collected headlines. They do not establish whether a claim is true. The AI generated summary is restricted to the collected material.
