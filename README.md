# Multi-Agent AI News Intelligence System

A Python 3.12 demonstration that collects technology headlines from RSS feeds, extracts article text, applies transparent quality and cross-source support heuristics, builds structured knowledge, filters technology stories, reports trends, and prints a Markdown digest. LangGraph runs each responsibility as a distinct stage.

## Installation

Use Python 3.12, create a virtual environment, and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`. Set `GROQ_API_KEY` to enable a separate AI summary for every collected technology story. The default model is `openai/gpt-oss-120b`; change `GROQ_MODEL` if you prefer another model enabled for your Groq account. Without a key, the app shows article excerpts instead. News collection uses the public BBC Technology RSS feed and does not require a news API key.

## Run

Launch the web UI:

```bash
streamlit run ui.py
```

Open the local URL Streamlit prints, then select **Fetch and analyze this week’s news**. The page shows the generated digest, trends, and article assessments.

Or run the workflow in the terminal:

```bash
python main.py
```

The program prints its digest and a collection count. It keeps articles published since Monday at 00:00 in the machine's local timezone, then scrapes each article page. Feed, scraping, and model errors are logged; failed page extraction falls back to the text included in the RSS entry. `MAX_ARTICLES_PER_FEED`, `REQUEST_TIMEOUT_SECONDS`, and `LOG_LEVEL` can be adjusted in `.env`.

## Architecture

- `app/agents/` contains focused research, validation, fact estimation, knowledge, technology filtering, trend, and summary agents.
- `app/utils/` contains feed loading, page extraction, deduplication, and heuristic scoring.
- `app/schemas.py` defines Pydantic data models; `app/state.py` defines the typed graph state.
- `app/graph.py` assembles the workflow; `main.py` invokes it and displays the result.

## LangGraph flow

```text
START → research → validation → fact_check → knowledge → tech_filter
      → trend_analysis → summary → END
```

Add a node with `build_graph(extra_nodes={"validation": my_node})` to insert it immediately after the named stage. The built-in agents do not need to be rewritten to extend the graph.

Credibility and truth values are explainable heuristics based on source identity, available article text and dates, and overlap between collected headlines. They do not establish whether a claim is true. The AI generated summary is restricted to the collected material.
