<div align="center">

# 🔎 Research Desk

### A multi-agent AI research assistant that searches, reads, writes and peer-reviews reports on any topic

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-agents-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--5--mini-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Tavily](https://img.shields.io/badge/Tavily-web%20search-0e8a8c)](https://tavily.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

<img src="docs/screenshots/home.png" alt="Research Desk home screen: topic input, example topics in the sidebar, and a four-step agent overview" width="900">

</div>

---

## Table of contents

- [Overview](#overview)
- [Problem statement](#problem-statement)
- [Key features](#key-features)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Usage](#usage)
- [Deployment](#deployment)
- [Design decisions](#design-decisions)
- [Roadmap](#roadmap)
- [Author](#author)

---

## Overview

**Research Desk** turns a single topic into a sourced, structured research report in a few minutes. Instead of one large prompt, it splits the work across **four specialised AI agents** that each do one job well. The same idea underpins most production agent systems:

| # | Agent | Responsibility | Tools |
|---|-------|----------------|-------|
| 1 | 🌐 **Search agent** | Finds recent, reliable sources on the topic | Tavily web search |
| 2 | 📄 **Reader agent** | Picks the most relevant source and scrapes it in depth | `requests` + BeautifulSoup |
| 3 | ✍️ **Writer** | Drafts a structured report (intro, key findings, conclusion, sources) | LLM chain |
| 4 | 🧐 **Critic** | Scores the report out of 10 and lists strengths and gaps | LLM chain |

The project ships with a polished **Streamlit web app** and a **command-line pipeline** that share the same agents.

## Problem statement

Researching an unfamiliar topic means hours of searching, opening tabs, skimming articles and stitching notes together. Asking a chatbot directly is faster but brings its own problems:

- **Stale knowledge.** The model only knows what it was trained on.
- **No sources.** Claims are hard to verify.
- **No quality check.** The output is never reviewed before you rely on it.

Research Desk addresses each of these. It grounds the report in **live web results**, reads a **primary source in full**, **cites URLs**, and runs every draft past an independent **critic agent**, so you can see how trustworthy the report is before you use it.

## Key features

- **Multi-agent pipeline.** Search → Read → Write → Review, with each agent focused on one task.
- **Live web grounding.** Tavily search returns fresh results, and the reader agent scrapes the best page for depth.
- **Structured, cited reports.** Every report has an introduction, at least three key findings, a conclusion and a source list.
- **Built-in quality review.** A critic agent returns a score out of 10, strengths, areas to improve and a one-line verdict.
- **Live progress tracking.** An animated four-step tracker and an expandable run log show which agent is working.
- **Results at a glance.** Metric tiles for critic score, source count, report length and run time.
- **Export.** Download any report as Markdown with one click.
- **Light and dark mode.** Custom components adapt to the Streamlit theme you choose.
- **Responsive.** Layouts adapt from wide desktop screens down to phones.
- **Accessible.** Visible keyboard focus, `aria-live` progress updates, labelled controls and `prefers-reduced-motion` support.
- **Safe rendering.** Scraped titles and snippets are HTML-escaped, and only `http(s)` links are rendered.
- **Configuration health check.** The sidebar shows whether the required API keys are set, without revealing them.

## Screenshots

| Light mode | Dark mode |
|:---:|:---:|
| <img src="docs/screenshots/home.png" alt="Research Desk in light mode" width="440"> | <img src="docs/screenshots/home-dark.png" alt="Research Desk in dark mode" width="440"> |

<p align="center">
  <img src="docs/screenshots/mobile.png" alt="Research Desk on a mobile screen" width="260"><br>
  <em>Mobile layout</em>
</p>

## Architecture

```mermaid
flowchart LR
    U([User topic]) --> S

    subgraph Pipeline["Research pipeline (agents.py)"]
        direction LR
        S["🌐 Search agent<br/><sub>LangChain agent + web_search tool</sub>"]
        R["📄 Reader agent<br/><sub>LangChain agent + url_scrape tool</sub>"]
        W["✍️ Writer<br/><sub>prompt | LLM | parser</sub>"]
        C["🧐 Critic<br/><sub>prompt | LLM | parser</sub>"]
        S -- "top results" --> R
        S -- "search summary" --> W
        R -- "scraped page" --> W
        W -- "draft report" --> C
    end

    S <-.-> T[(Tavily API)]
    R <-.-> WEB[(Source web page)]
    S & R & W & C <-.-> O[(OpenAI gpt-5-mini)]

    W --> OUT([Report])
    C --> OUT2([Score + review])
```

**How data flows**

1. **Search agent:** a tool-calling agent built with `langchain.agents.create_agent`. It decides how to query the `web_search` tool, which wraps Tavily and returns the title, URL and a snippet for the top three results.
2. **Reader agent:** a second agent that receives the search summary, chooses the most relevant URL and calls `url_scrape`. That tool fetches the page, strips scripts, styles, navigation and footers, and returns up to 3,000 characters of clean text.
3. **Writer:** an LCEL chain (`ChatPromptTemplate | ChatOpenAI | StrOutputParser`) that combines the search results and scraped content into a structured Markdown report.
4. **Critic:** a second LCEL chain that evaluates the report against a fixed rubric. The UI parses its output into the score badge and review sections.

The Streamlit UI (`main.py`) and the CLI (`pipeline.py`) orchestrate the same four steps, so the agents are defined once in `agents.py` and reused.

## Tech stack

| Layer | Technology |
|-------|------------|
| LLM | OpenAI `gpt-5-mini` via `langchain-openai` |
| Agent framework | LangChain (`create_agent`, LCEL chains), LangGraph runtime |
| Web search | Tavily (`tavily-python`) |
| Scraping | `requests`, BeautifulSoup 4 |
| Frontend | Streamlit (custom CSS, native status, pills, metrics and tabs) |
| Config | `python-dotenv`, `.streamlit/config.toml` |
| Tooling | `uv` / `pip`, `pyproject.toml` |

## Project structure

```
MultiAgentSystem/
├── main.py               # Streamlit web app: UI, progress tracking, results view
├── pipeline.py           # Command-line version of the same four-step pipeline
├── agents.py             # LLM, search and reader agents, writer and critic chains
├── tools.py              # LangChain tools: Tavily web_search and url_scrape
├── .streamlit/
│   └── config.toml       # Theme (brand colours) and server settings
├── docs/
│   └── screenshots/      # Images used in this README
├── src/multiagentsystem/ # Package entry point (uv project scaffold)
├── .env.example          # Template for required API keys
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
└── README.md
```

## Getting started

### Prerequisites

- Python **3.10+** (the project pins 3.14 in `.python-version`)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Tavily API key](https://app.tavily.com) (the free tier is enough)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/bhoomikaaa20/MultiAgentSystem.git
cd MultiAgentSystem

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API keys
cp .env.example .env      # then edit .env with your keys
```

<details>
<summary>Using <code>uv</code> instead of pip</summary>

```bash
uv venv
uv pip install -r requirements.txt
```
</details>

## Environment variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `OPENAI_API_KEY` | ✅ | Authenticates the OpenAI model used by all four agents. |
| `TAVILY_API_KEY` | ✅ | Authenticates Tavily web search for the search agent. |

Keys are loaded from `.env` by `python-dotenv` at startup. `.env` is listed in `.gitignore`, so never commit it. The app's sidebar shows whether each key is **set** or **missing** and never displays its value.

## Usage

### Web app

```bash
streamlit run main.py
```

Open <http://localhost:8501>, enter a topic or pick an example from the sidebar, and click **Run research**. A run usually takes one to three minutes. Once it finishes you can:

- read the report and **download it as Markdown**
- open **Critic review** for the score and feedback
- browse **Sources** to see every result the search agent found
- check **Scraped page** to see exactly what the reader agent read

### Command line

```bash
python pipeline.py
# Enter a research topic: State of open-source LLMs
```

Each step's output prints to the terminal as the pipeline runs.

## Deployment

### Streamlit Community Cloud (free)

1. Push the repository to GitHub. `.env` is gitignored and stays local.
2. Go to [share.streamlit.io](https://share.streamlit.io), click **New app** and select this repository, with `main.py` as the entry point.
3. Under **Advanced settings → Secrets**, add your keys:
   ```toml
   OPENAI_API_KEY = "sk-..."
   TAVILY_API_KEY = "tvly-..."
   ```
   Streamlit exposes top-level secrets as environment variables, so no code changes are needed.
4. Click **Deploy**.

### Any server or container platform (Render, Railway, a VM, …)

Install the dependencies, set the two environment variables in the platform's dashboard, and start the app with:

```bash
streamlit run main.py --server.port $PORT --server.address 0.0.0.0
```

## Design decisions

- **Specialised agents instead of one prompt.** Smaller, focused prompts are easier to debug and to evaluate, and each step can be swapped out independently.
- **A separate critic.** Self-review in the same prompt tends to be lenient. A separate chain with its own rubric gives a more honest score.
- **A truncated hand-off between agents.** The reader agent receives only the first 800 characters of the search summary, and scraped pages are capped at 3,000 characters. This keeps token costs and latency predictable.
- **One set of agents, two front ends.** The UI and CLI import the same objects from `agents.py`, so behaviour stays consistent.

## Roadmap

- [ ] Stream report tokens to the UI as they are generated
- [ ] Scrape and merge several sources instead of one
- [ ] Let the critic's feedback trigger an automatic revision pass
- [ ] Keep a history of past reports with search
- [ ] Export to PDF and DOCX

## Author

**Bhoomika Somavarapu** · [GitHub @bhoomikaaa20](https://github.com/bhoomikaaa20)

If you found this project interesting, consider giving it a ⭐.
