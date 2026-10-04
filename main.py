import re
import time

import streamlit as st

# agents.py already calls load_dotenv(), so API keys from .env are loaded here
from agents import (
    web_search_agent,
    url_scrape_agent,
    report_chain,
    critic_chain,
)

# ---------------------------------------------------------------- page setup
st.set_page_config(
    page_title="Research Desk",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

STEPS = [
    ("Search", "Finding recent sources"),
    ("Read", "Scraping the best page"),
    ("Write", "Drafting the report"),
    ("Review", "Critiquing the draft"),
]

EXAMPLES = [
    "Solid-state batteries in electric vehicles",
    "Impact of GLP-1 drugs on the food industry",
    "State of open-source LLMs",
    "Quantum error correction progress",
]

# ----------------------------------------------------------------- styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #14283f;
    --muted: #5b6b7f;
    --line: #dde4ec;
    --bg: #f5f7fa;
    --card: #ffffff;
    --accent: #0e8a8c;
    --accent-soft: #e2f4f4;
}

html, body, [class*="css"], .stMarkdown, .stTextInput input, button {
    font-family: 'Manrope', system-ui, sans-serif !important;
}
.stApp { background: var(--bg); }
.block-container { padding-top: 2.2rem; max-width: 1100px; }
#MainMenu, footer { visibility: hidden; }

.hero h1 {
    font-size: 2.4rem; font-weight: 800; color: var(--ink);
    letter-spacing: -0.02em; margin: 0 0 .3rem 0;
}
.hero p { color: var(--muted); font-size: 1.05rem; margin: 0 0 1.4rem 0; max-width: 60ch; }

.stTextInput input {
    border-radius: 12px; border: 1.5px solid var(--line);
    padding: .85rem 1rem; font-size: 1.02rem; background: var(--card);
}
.stTextInput input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }

.stButton > button[kind="primary"], .stDownloadButton > button {
    background: var(--accent); color: #fff; border: none; border-radius: 12px;
    padding: .8rem 1.4rem; font-weight: 700; width: 100%;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    background: #0b7173; color: #fff;
}
section[data-testid="stSidebar"] { background: #eef2f6; border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] .stButton > button {
    text-align: left; border-radius: 10px; border: 1px solid var(--line);
    background: var(--card); color: var(--ink); font-weight: 500; width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: var(--accent); color: var(--accent);
}

.tracker { display: flex; gap: .75rem; margin: 1.2rem 0 1.4rem 0; }
.tstep {
    flex: 1; padding: .85rem 1rem; border-radius: 12px;
    background: var(--card); border: 1.5px solid var(--line);
}
.tstep .name { font-weight: 700; color: var(--muted); font-size: .98rem; }
.tstep .desc { color: var(--muted); font-size: .85rem; margin-top: .15rem; }
.tstep.done { border-color: var(--accent); background: var(--accent-soft); }
.tstep.done .name { color: var(--accent); }
.tstep.done .name::before { content: "✓ "; }
.tstep.active { border-color: var(--ink); }
.tstep.active .name { color: var(--ink); }
.tstep.active .name::after { content: " …"; }
@media (max-width: 700px) { .tracker { flex-direction: column; } }

.paper {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    padding: 1.6rem 2rem;
}
.meta { color: var(--muted); font-size: .9rem; margin-bottom: .8rem; }
.stTabs [data-baseweb="tab-list"] { gap: .4rem; }
.stTabs [data-baseweb="tab"] { font-weight: 600; }

.source {
    background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: .9rem 1.1rem; margin-bottom: .7rem;
}
.source a { color: var(--ink); font-weight: 700; text-decoration: none; }
.source a:hover { color: var(--accent); text-decoration: underline; }
.source .host { color: var(--muted); font-size: .82rem; margin: .1rem 0 .35rem 0; }
.source .snip { color: var(--ink); font-size: .92rem; }

.score {
    display: inline-block; background: var(--accent-soft); color: var(--accent);
    border-radius: 12px; padding: .5rem 1rem; font-weight: 800; font-size: 1.6rem;
    margin-bottom: 1rem;
}
.score small { font-size: .95rem; font-weight: 600; color: var(--muted); }
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------- helpers
def tracker_html(done: int, active: int | None) -> str:
    cells = []
    for i, (name, desc) in enumerate(STEPS):
        cls = "done" if i < done else ("active" if i == active else "")
        cells.append(
            f'<div class="tstep {cls}"><div class="name">{name}</div>'
            f'<div class="desc">{desc}</div></div>'
        )
    return f'<div class="tracker">{"".join(cells)}</div>'


def to_text(content) -> str:
    """Message content can be a string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return str(content)


def tool_outputs(messages, tool_name: str) -> list[str]:
    """Raw outputs returned by a tool inside an agent run."""
    return [
        to_text(m.content)
        for m in messages
        if getattr(m, "type", "") == "tool" and getattr(m, "name", "") == tool_name
    ]


def scraped_url(messages) -> str | None:
    """The URL the reader agent chose to scrape."""
    for m in messages:
        for call in getattr(m, "tool_calls", None) or []:
            if call.get("name") == "url_scrape":
                return call.get("args", {}).get("url")
    return None


def parse_sources(raw_blocks: list[str]) -> list[dict]:
    """Parse the 'Title / URL / Content' format produced by tools.web_search."""
    sources = []
    for block in raw_blocks:
        for chunk in block.split("\n---\n"):
            title = re.search(r"Title:\s*(.*)", chunk)
            url = re.search(r"URL:\s*(\S+)", chunk)
            content = re.search(r"Content:\s*(.*)", chunk, re.DOTALL)
            if url:
                sources.append(
                    {
                        "title": title.group(1).strip() if title else url.group(1),
                        "url": url.group(1).strip(),
                        "content": content.group(1).strip() if content else "",
                    }
                )
    return sources


def host_of(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def split_critic(text: str) -> tuple[str | None, str]:
    """Pull the 'Score: X/10' line out and tidy the rest for markdown."""
    score = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", text)
    body = re.sub(r"^\s*Score:.*$", "", text, count=1, flags=re.MULTILINE).strip()
    body = re.sub(
        r"^(Strengths|Areas to Improve|One line verdict):?\s*$",
        r"**\1**\n",
        body,
        flags=re.MULTILINE,
    )
    body = re.sub(r"^(One line verdict):\s*(\S.*)$", r"**\1**\n\n\2", body, flags=re.MULTILINE)
    return (score.group(1) if score else None), body


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "report"


def set_topic(value: str) -> None:
    st.session_state["topic"] = value


def run_pipeline(topic: str, tracker_slot) -> dict:
    """Same four steps as pipeline.py, with progress shown in the UI."""
    state = {}

    def show(done, active=None):
        tracker_slot.markdown(tracker_html(done, active), unsafe_allow_html=True)

    # Step 1 - Search agent
    show(0, 0)
    search = web_search_agent.invoke(
        {
            "messages": [
                (
                    "user",
                    f"Find recent, reliable and detailed information about: {topic}",
                )
            ]
        }
    )
    state["search_res"] = to_text(search["messages"][-1].content)
    state["sources"] = parse_sources(tool_outputs(search["messages"], "web_search"))

    # Step 2 - Reader agent
    show(1, 1)
    scrape = url_scrape_agent.invoke(
        {
            "messages": [
                (
                    "user",
                    f"""Based on the following search results about '{topic}',
pick the most relevant URL and scrape it for deeper content.

Search Results:
{state["search_res"][:800]}""",
                )
            ]
        }
    )
    state["scrape_res"] = to_text(scrape["messages"][-1].content)
    state["scraped_url"] = scraped_url(scrape["messages"])

    # Step 3 - Writer
    show(2, 2)
    research_combined = (
        f"SEARCH RESULTS:\n{state['search_res']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scrape_res']}"
    )
    state["report"] = report_chain.invoke({"topic": topic, "research": research_combined})

    # Step 4 - Critic
    show(3, 3)
    state["critic"] = critic_chain.invoke({"report": state["report"]})

    show(4, None)
    return state


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### Try an example")
    for ex in EXAMPLES:
        st.button(ex, key=f"ex_{ex}", on_click=set_topic, args=(ex,))

    st.markdown("---")
    st.markdown("### How it works")
    st.caption(
        "Four AI agents work in sequence: one searches the web, one reads the "
        "best source in depth, one writes the report, and one reviews it."
    )
    st.caption("A run usually takes one to three minutes.")

# -------------------------------------------------------------------- hero
st.markdown(
    """
<div class="hero">
    <h1>Research Desk</h1>
    <p>Enter a topic and get a sourced, reviewed report from a team of AI agents.</p>
</div>
""",
    unsafe_allow_html=True,
)

col_input, col_btn = st.columns([5, 1.3], vertical_alignment="bottom")
with col_input:
    topic = st.text_input(
        "Research topic",
        key="topic",
        placeholder="e.g. Impact of solid-state batteries on EV range",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("Run research", type="primary")

# --------------------------------------------------------------------- run
if run:
    if not topic.strip():
        st.warning("Enter a topic to research.")
    else:
        tracker_slot = st.empty()
        started = time.time()
        try:
            state = run_pipeline(topic.strip(), tracker_slot)
            st.session_state["result"] = {
                "topic": topic.strip(),
                "state": state,
                "seconds": time.time() - started,
            }
        except Exception as exc:
            tracker_slot.empty()
            st.session_state.pop("result", None)
            st.error(
                f"The research run failed: {exc}\n\n"
                "Check OPENAI_API_KEY and TAVILY_API_KEY in your `.env` file "
                "and your internet connection, then try again."
            )

# ----------------------------------------------------------------- results
saved = st.session_state.get("result")

if saved:
    state = saved["state"]
    report = str(state.get("report", ""))
    score, critic_body = split_critic(str(state.get("critic", "")))

    st.markdown(
        f'<div class="meta">Report on <b>{saved["topic"]}</b> · '
        f'finished in {saved["seconds"]:.0f}s</div>',
        unsafe_allow_html=True,
    )

    tab_report, tab_critic, tab_sources, tab_scrape = st.tabs(
        ["Report", "Critic review", "Sources", "Scraped page"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(report)
        st.write("")
        _, dl_col = st.columns([4, 1.4])
        with dl_col:
            st.download_button(
                "Download report",
                data=report,
                file_name=f"{slugify(saved['topic'])}.md",
                mime="text/markdown",
            )

    with tab_critic:
        with st.container(border=True):
            if score:
                st.markdown(
                    f'<div class="score">{score}<small> / 10</small></div>',
                    unsafe_allow_html=True,
                )
            st.markdown(critic_body)

    with tab_sources:
        sources = state.get("sources", [])
        if sources:
            for s in sources:
                st.markdown(
                    f'<div class="source"><a href="{s["url"]}" target="_blank">{s["title"]}</a>'
                    f'<div class="host">{host_of(s["url"])}</div>'
                    f'<div class="snip">{s["content"]}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            with st.container(border=True):
                st.markdown(str(state.get("search_res", "")))

    with tab_scrape:
        if state.get("scraped_url"):
            st.markdown(f"Page read by the reader agent: [{state['scraped_url']}]({state['scraped_url']})")
        with st.container(border=True):
            st.markdown(str(state.get("scrape_res", "")))

else:
    st.info("Your report will appear here. Pick an example from the sidebar or type your own topic.")
