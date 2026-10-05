# Multi-Agent AI News Intelligence System

A Python 3.12 demonstration that collects technology headlines from RSS feeds, extracts article text, applies transparent quality and cross-source support heuristics, builds structured knowledge, filters technology stories, reports trends, and prints a Markdown digest. LangGraph runs each responsibility as a distinct stage.

## Installation

Use Python 3.12, create a virtual environment, and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`. Set `GROQ_API_KEY` to enable autonomous source selection and Groq summaries for every collected technology story. The default model is `openai/gpt-oss-120b`; change `GROQ_MODEL` if you prefer another model enabled for your Groq account. A Groq key is required to generate a digest with technology stories; the app reports an error instead of substituting raw article excerpts when Groq is unavailable. Streamlit deployments can provide `GROQ_API_KEY` and `GROQ_MODEL` through `st.secrets`. News collection uses public RSS feeds and does not require a news API key.

## Run

Launch the web UI:

```bash
streamlit run ui.py
```

Open the local URL Streamlit prints, then select **Fetch and analyze this week’s news**. The page shows the generated digest, trends, and article assessments.

The UI saves a compressed daily digest in a browser cookie. That browser reuses the saved digest after refresh and cannot generate another one until midnight in `APP_TIMEZONE` (defaults to `Asia/Kathmandu`). The cookie includes the digest and trends; article assessments are included when they fit. Large digests are shortened to stay within browser cookie limits. Clearing cookies or using another browser starts a separate daily cache.

Or run the workflow in the terminal:

```bash
python main.py
```

The program prints its digest and a collection count. It keeps articles published since Monday at 00:00 in the machine's local timezone, then scrapes each article page. Feed, scraping, and model errors are logged; failed page extraction falls back to the text included in the RSS entry. `MAX_ARTICLES_PER_FEED`, `REQUEST_TIMEOUT_SECONDS`, and `LOG_LEVEL` can be adjusted in `.env`.

## Architecture

- `app/agents/` contains the research planner and focused analysis agents.
- `app/prompts/` holds agent role prompts. The planner and writer prompts are loaded into LLM calls.
- `app/orchestrator/` routes workflow stages and executes the analysis nodes; `app/workflows/` exposes the runnable research workflow.
- `app/tools/` wraps RSS loading and article enrichment; `app/utils/` provides feed parsing, scraping, deduplication, and scoring helpers.
- `app/memory/short_term.py` creates per-run state. `app/state.py` defines its type and `app/schemas.py` defines Pydantic data models.
- `app/models/llm.py` centralizes chat model setup. `main.py` and `ui.py` invoke the workflow.

This project uses in-memory workflow state and public RSS/article pages, so it does not include persistent databases, vector storage, arbitrary filesystem tools, or a scheduled background worker.

## LangGraph flow

```text
START → research_planner ⇄ collect (up to MAX_RESEARCH_ROUNDS)
      → validation → fact_check → knowledge → tech_filter
      → trend_analysis → summary → END
```

The planner chooses whether another configured source is useful and selects only from the allowlisted RSS feeds in `app/config.py`. The loop has a configurable upper bound (`MAX_RESEARCH_ROUNDS`, default 3), so a model response cannot trigger unbounded browsing or arbitrary URL fetching. Analysis stages then run after collection finishes.

Add a node with `build_graph(extra_nodes={"validation": my_node})` to insert it immediately after the named stage. The built-in agents do not need to be rewritten to extend the graph.

Credibility and truth values are explainable heuristics based on source identity, available article text and dates, and overlap between collected headlines. They do not establish whether a claim is true. The AI generated summary is restricted to the collected material.
