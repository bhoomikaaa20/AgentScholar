import html
import os
import re
import time

import openai
import requests
import streamlit as st
from tavily.errors import InvalidAPIKeyError, MissingAPIKeyError, UsageLimitExceededError

# agents.py already calls load_dotenv(), so API keys from .env are loaded here
from agents import (
    web_search_agent,
    url_scrape_agent,
    report_chain,
    critic_chain,
)

REPO_URL = "https://github.com/bhoomikaaa20/MultiAgentSystem"

# ---------------------------------------------------------------- page setup
st.set_page_config(
    page_title="AgentScholar · Multi-Agent AI Research Assistant",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": REPO_URL,
        "Report a bug": f"{REPO_URL}/issues",
        "About": "AgentScholar — a multi-agent research assistant built with LangChain, OpenAI and Tavily.",
    },
)

STEPS = [
    ("Search", "Finding recent sources", "🌐"),
    ("Read", "Scraping the best page", "📄"),
    ("Write", "Drafting the report", "✍️"),
    ("Review", "Critiquing the draft", "🧐"),
]

EXAMPLES = [
    "Solid-state batteries in electric vehicles",
    "Impact of GLP-1 drugs on the food industry",
    "State of open-source LLMs",
    "Quantum error correction progress",
]

REQUIRED_KEYS = ["OPENAI_API_KEY", "TAVILY_API_KEY"]

# ----------------------------------------------------------------- styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --bg: #07080f;
    --ink: #e7e9f4;
    --muted: #9097b3;
    --faint: #5d6383;
    --line: rgba(255, 255, 255, .08);
    --line-strong: rgba(255, 255, 255, .16);
    --glass: rgba(255, 255, 255, .035);
    --glass-hi: rgba(255, 255, 255, .06);
    --violet: #8b5cf6;
    --cyan: #22d3ee;
    --pink: #f472b6;
    --green: #34d399;
    --amber: #fbbf24;
    --red: #f87171;
    --grad: linear-gradient(120deg, var(--violet) 0%, var(--cyan) 100%);
    --radius: 18px;
    --glow: 0 0 0 1px rgba(139, 92, 246, .35), 0 10px 40px -10px rgba(139, 92, 246, .55);
}

/* Streamlit's Material icons are ligature spans marked translate="no"; overriding their font prints the icon name. */
html, body, [class*="st-"]:not([translate="no"]), .stMarkdown, button, input, textarea {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
span[translate="no"][data-testid] { font-family: 'Material Symbols Rounded' !important; }
code, pre, .mono { font-family: 'JetBrains Mono', ui-monospace, monospace !important; }

/* ---------- aurora background ---------- */
.stApp {
    background:
        radial-gradient(900px 520px at 8% -8%, rgba(139, 92, 246, .22), transparent 60%),
        radial-gradient(760px 480px at 100% 0%, rgba(34, 211, 238, .14), transparent 60%),
        radial-gradient(700px 600px at 50% 120%, rgba(244, 114, 182, .08), transparent 60%),
        var(--bg);
    background-attachment: fixed;
}
.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 30%, transparent 75%);
    -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 30%, transparent 75%);
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1160px; position: relative; z-index: 1; }
footer { visibility: hidden; }
::selection { background: rgba(139, 92, 246, .45); }

a:focus-visible, button:focus-visible, input:focus-visible, [role="tab"]:focus-visible {
    outline: 2px solid var(--cyan) !important; outline-offset: 2px;
}

/* ---------- hero ---------- */
.hero { padding: .2rem 0 1.6rem 0; animation: rise .6s cubic-bezier(.2,.8,.2,1) both; }
.eyebrow {
    display: inline-flex; align-items: center; gap: .55rem;
    font-size: .74rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
    color: #c4b5fd; padding: .38rem .85rem .38rem .6rem; border-radius: 999px; margin-bottom: 1.2rem;
    background: rgba(139, 92, 246, .1); border: 1px solid rgba(139, 92, 246, .3);
    backdrop-filter: blur(8px);
}
.eyebrow .live {
    width: 8px; height: 8px; border-radius: 50%; background: var(--green);
    box-shadow: 0 0 0 0 rgba(52, 211, 153, .7); animation: ping 2s infinite;
}
.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.6rem); font-weight: 800; color: var(--ink);
    letter-spacing: -0.035em; line-height: 1.04; margin: 0 0 .9rem 0; padding: 0;
}
.hero h1 .grad {
    background: linear-gradient(100deg, #a78bfa, #22d3ee, #f472b6, #a78bfa);
    background-size: 300% 100%; animation: shimmer 8s linear infinite;
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--muted); font-size: 1.1rem; margin: 0; max-width: 60ch; line-height: 1.6; }
.chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.3rem; }
.chip {
    font-size: .8rem; color: var(--muted); padding: .35rem .75rem; border-radius: 999px;
    background: var(--glass); border: 1px solid var(--line);
}
.chip b { color: var(--ink); font-weight: 600; }

/* ---------- command bar ---------- */
div[data-testid="stForm"] {
    background: linear-gradient(var(--glass-hi), var(--glass)) padding-box,
                linear-gradient(120deg, rgba(139,92,246,.6), rgba(34,211,238,.35), rgba(255,255,255,.06)) border-box;
    border: 1px solid transparent !important; border-radius: 20px; padding: .55rem .6rem !important;
    box-shadow: 0 20px 60px -25px rgba(139, 92, 246, .55); backdrop-filter: blur(14px);
}
.stTextInput input {
    background: transparent !important; border: none !important; box-shadow: none !important;
    padding: .9rem 1rem; font-size: 1.05rem; color: var(--ink);
}
.stTextInput input::placeholder { color: var(--faint); }
.stTextInput div[data-baseweb="input"], .stTextInput div[data-baseweb="base-input"] {
    background: transparent !important; border: none !important;
}

.stButton > button[kind="primary"], button[data-testid="stBaseButton-primaryFormSubmit"], .stDownloadButton > button {
    background: var(--grad) !important; color: #fff !important; border: none !important; border-radius: 14px;
    padding: .8rem 1.4rem; font-weight: 700; letter-spacing: .01em;
    box-shadow: 0 8px 24px -8px rgba(139, 92, 246, .8), inset 0 1px 0 rgba(255,255,255,.25);
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
}
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px); filter: brightness(1.1);
    box-shadow: 0 14px 32px -8px rgba(34, 211, 238, .6), inset 0 1px 0 rgba(255,255,255,.3);
}
button[data-testid="stBaseButton-primaryFormSubmit"]:active { transform: translateY(0); }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: rgba(10, 11, 20, .75) !important; backdrop-filter: blur(18px);
    border-right: 1px solid var(--line);
}
.brand { display: flex; align-items: center; gap: .75rem; margin: .2rem 0 1.4rem 0; }
.brand .logo {
    width: 42px; height: 42px; border-radius: 13px; display: grid; place-items: center; font-size: 1.2rem;
    background: var(--grad); box-shadow: 0 8px 22px -6px rgba(139, 92, 246, .8);
}
.brand .name { font-weight: 800; font-size: 1.1rem; color: var(--ink); line-height: 1.1; letter-spacing: -.01em; }
.brand .tag { font-size: .76rem; color: var(--muted); }
.side-label {
    font-size: .7rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase;
    color: var(--faint); margin: 1.5rem 0 .65rem 0;
}
.flow { list-style: none; padding: 0; margin: 0; position: relative; }
.flow::before {
    content: ""; position: absolute; left: 11px; top: 12px; bottom: 12px; width: 1px;
    background: linear-gradient(var(--violet), var(--cyan)); opacity: .5;
}
.flow li { display: flex; gap: .7rem; align-items: flex-start; margin: 0 0 .85rem 0; font-size: .9rem; color: var(--ink); position: relative; }
.flow .ix {
    flex: none; width: 23px; height: 23px; border-radius: 50%; display: grid; place-items: center;
    font-size: .7rem; font-weight: 800; color: #fff; background: #1a1c2e; border: 1px solid var(--line-strong);
}
.flow .sub { color: var(--muted); font-size: .8rem; }
.health {
    display: flex; align-items: center; gap: .6rem; font-size: .84rem; color: var(--ink);
    padding: .55rem .7rem; border-radius: 12px; background: var(--glass); border: 1px solid var(--line); margin: 0 0 .45rem 0;
}
.health code { font-size: .76rem; background: none; color: var(--ink); padding: 0; }
.health .st { margin-left: auto; font-size: .72rem; font-weight: 700; padding: .12rem .5rem; border-radius: 999px; }
.health .pip { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.ok   .pip { background: var(--green); box-shadow: 0 0 10px var(--green); }
.ok   .st  { color: var(--green); background: rgba(52, 211, 153, .12); }
.bad  .pip { background: var(--red); box-shadow: 0 0 10px var(--red); }
.bad  .st  { color: var(--red); background: rgba(248, 113, 113, .12); }
.warn .pip { background: var(--amber); }
.warn .st  { color: var(--amber); background: rgba(251, 191, 36, .12); }

/* ---------- agent pipeline stepper ---------- */
.tracker { display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin: 1.6rem 0 1.1rem 0; }
.tstep {
    position: relative; padding: 1rem 1.05rem; border-radius: var(--radius);
    background: var(--glass); border: 1px solid var(--line); backdrop-filter: blur(10px);
    transition: border-color .3s ease, background .3s ease, box-shadow .3s ease, opacity .3s ease;
    opacity: .6; overflow: hidden;
}
.tstep:not(:last-child)::before {
    content: ""; position: absolute; top: 50%; right: -.9rem; width: .9rem; height: 1px; background: var(--line-strong);
}
.tstep .top { display: flex; align-items: center; gap: .55rem; }
.tstep .ico {
    width: 32px; height: 32px; border-radius: 10px; display: grid; place-items: center; font-size: 1rem;
    background: rgba(255, 255, 255, .05); border: 1px solid var(--line);
}
.tstep .name { font-weight: 700; color: var(--ink); font-size: .96rem; }
.tstep .desc { color: var(--muted); font-size: .8rem; margin-top: .55rem; }
.tstep .state { margin-left: auto; font-size: .7rem; font-weight: 700; color: var(--faint); letter-spacing: .04em; text-transform: uppercase; }
.tstep.done { opacity: 1; border-color: rgba(52, 211, 153, .35); background: rgba(52, 211, 153, .06); }
.tstep.done .state { color: var(--green); }
.tstep.active { opacity: 1; border-color: rgba(139, 92, 246, .6); background: rgba(139, 92, 246, .1); box-shadow: var(--glow); }
.tstep.active .ico { background: var(--grad); border-color: transparent; }
.tstep.active::after {
    content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), var(--violet), transparent);
    background-size: 200% 100%; animation: sweep 1.3s linear infinite;
}
.pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); animation: pulse 1.1s ease-in-out infinite; }

/* ---------- results ---------- */
.meta { color: var(--muted); font-size: .92rem; margin: 2rem 0 1rem 0; display: flex; align-items: center; gap: .6rem; }
.meta b { color: var(--ink); font-weight: 650; }
.meta .tag { font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--green);
    background: rgba(52, 211, 153, .12); padding: .2rem .55rem; border-radius: 999px; }
div[data-testid="stMetric"] {
    background: var(--glass); border: 1px solid var(--line); border-radius: var(--radius);
    padding: 1rem 1.2rem; backdrop-filter: blur(10px); position: relative; overflow: hidden;
    transition: border-color .2s ease, transform .2s ease;
}
div[data-testid="stMetric"]::before {
    content: ""; position: absolute; inset: 0 0 auto 0; height: 2px; background: var(--grad); opacity: .7;
}
div[data-testid="stMetric"]:hover { border-color: var(--line-strong); transform: translateY(-2px); }
div[data-testid="stMetricLabel"] p { font-weight: 600; color: var(--muted); font-size: .8rem; letter-spacing: .02em; }
div[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -.02em; }

.stTabs [data-baseweb="tab-list"] {
    gap: .3rem; border-bottom: none; background: var(--glass); border: 1px solid var(--line);
    padding: .3rem; border-radius: 14px; width: fit-content; max-width: 100%; overflow-x: auto;
}
.stTabs [data-baseweb="tab"] { font-weight: 600; padding: .5rem .95rem; border-radius: 10px; height: auto; }
.stTabs [aria-selected="true"] { background: rgba(139, 92, 246, .18); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--radius) !important; border-color: var(--line) !important;
    background: var(--glass); backdrop-filter: blur(10px);
}

.source {
    display: block; background: var(--glass); border: 1px solid var(--line); border-radius: 16px;
    padding: 1rem 1.2rem; margin-bottom: .75rem; text-decoration: none !important; color: inherit !important;
    transition: border-color .2s ease, transform .2s ease, background .2s ease;
}
.source:hover { border-color: rgba(34, 211, 238, .5); background: rgba(34, 211, 238, .05); transform: translateX(3px); }
.source .num {
    display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 8px;
    background: var(--grad); color: #fff; font-size: .72rem; font-weight: 800; margin-right: .6rem;
}
.source .title { color: var(--ink); font-weight: 650; }
.source .host { color: var(--cyan); font-size: .78rem; font-weight: 600; margin: .4rem 0 .35rem 0; }
.source .snip { color: var(--muted); font-size: .88rem; line-height: 1.55; }

.score-wrap { display: flex; align-items: center; gap: 1.2rem; margin-bottom: 1.1rem; flex-wrap: wrap; }
.ring {
    --v: 0; width: 92px; height: 92px; border-radius: 50%; display: grid; place-items: center; flex: none;
    background: conic-gradient(var(--tone) calc(var(--v) * 1%), rgba(255,255,255,.07) 0);
}
.ring > div {
    width: 74px; height: 74px; border-radius: 50%; background: #0d0f1a; display: grid; place-items: center;
    font-weight: 800; font-size: 1.5rem; color: var(--ink); line-height: 1;
}
.ring small { display: block; font-size: .65rem; color: var(--muted); font-weight: 600; text-align: center; }
.ring.good { --tone: var(--green); } .ring.mid { --tone: var(--amber); } .ring.low { --tone: var(--red); }
.score-copy b { display: block; color: var(--ink); font-size: 1.05rem; }
.score-copy span { color: var(--muted); font-size: .88rem; }

/* ---------- error card ---------- */
.err {
    border: 1px solid rgba(248, 113, 113, .35); background: rgba(248, 113, 113, .07);
    border-radius: var(--radius); padding: 1.1rem 1.25rem; margin: 1.2rem 0;
}
.err b { color: #fecaca; display: block; margin-bottom: .3rem; font-size: 1rem; }
.err p { color: var(--muted); margin: .2rem 0; font-size: .9rem; line-height: 1.55; }
.err code { color: var(--ink); }
.err a { color: var(--cyan); }

/* ---------- empty state ---------- */
.empty { margin-top: 2rem; animation: rise .6s cubic-bezier(.2,.8,.2,1) .1s both; }
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem; }
.feature {
    background: var(--glass); border: 1px solid var(--line); border-radius: var(--radius);
    padding: 1.3rem 1.3rem; backdrop-filter: blur(10px); position: relative; overflow: hidden;
    transition: border-color .25s ease, transform .25s ease;
}
.feature::after {
    content: ""; position: absolute; width: 160px; height: 160px; right: -60px; top: -60px; border-radius: 50%;
    background: radial-gradient(circle, rgba(139, 92, 246, .22), transparent 70%);
}
.feature:hover { border-color: rgba(139, 92, 246, .45); transform: translateY(-3px); }
.feature .fi {
    width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 1.2rem;
    background: rgba(255,255,255,.05); border: 1px solid var(--line);
}
.feature b { display: block; color: var(--ink); margin: .9rem 0 .3rem 0; font-size: 1rem; }
.feature span.d { color: var(--muted); font-size: .87rem; line-height: 1.5; }
.empty-note { text-align: center; color: var(--faint); font-size: .88rem; margin-top: 1.4rem; }

.app-footer {
    margin-top: 3.5rem; padding-top: 1.2rem; border-top: 1px solid var(--line);
    color: var(--faint); font-size: .82rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: .5rem;
}
.app-footer a { color: var(--muted); text-decoration: none; font-weight: 600; }
.app-footer a:hover { color: var(--cyan); }

@keyframes rise { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes sweep { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .3; transform: scale(.7); } }
@keyframes shimmer { from { background-position: 0% 50%; } to { background-position: 300% 50%; } }
@keyframes ping { 0% { box-shadow: 0 0 0 0 rgba(52,211,153,.6); } 80%, 100% { box-shadow: 0 0 0 8px rgba(52,211,153,0); } }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ---------- responsive ---------- */
@media (max-width: 900px) {
    .tracker { grid-template-columns: repeat(2, 1fr); }
    .tstep::before { display: none; }
    .features { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem; }
    .tracker { grid-template-columns: 1fr; }
    .hero p { font-size: 1rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------- helpers
def esc(value) -> str:
    return html.escape(str(value), quote=True)


def tracker_html(done: int, active: int | None) -> str:
    cells = []
    for i, (name, desc, icon) in enumerate(STEPS):
        if i < done:
            cls, state = "done", "✓ Done"
        elif i == active:
            cls, state = "active", '<span class="pulse" aria-hidden="true"></span>'
        else:
            cls, state = "", "Queued"
        cells.append(
            f'<div class="tstep {cls}">'
            f'<div class="top"><span class="ico" aria-hidden="true">{icon}</span>'
            f'<span class="name">{name}</span><span class="state">{state}</span></div>'
            f'<div class="desc">{desc}</div></div>'
        )
    if active is not None:
        label = f"Step {active + 1} of {len(STEPS)}: {STEPS[active][1]}"
    else:
        label = "All steps complete"
    return (
        f'<div class="tracker" role="status" aria-live="polite" aria-label="{label}">'
        f'{"".join(cells)}</div>'
    )


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
    seen = set()
    for block in raw_blocks:
        for chunk in block.split("\n---\n"):
            title = re.search(r"Title:\s*(.*)", chunk)
            url = re.search(r"URL:\s*(\S+)", chunk)
            content = re.search(r"Content:\s*(.*)", chunk, re.DOTALL)
            if url and url.group(1).strip() not in seen:
                seen.add(url.group(1).strip())
                sources.append(
                    {
                        "title": title.group(1).strip() if title else url.group(1),
                        "url": url.group(1).strip(),
                        "content": content.group(1).strip() if content else "",
                    }
                )
    return sources


def one_line(text: str) -> str:
    # A newline inside st.markdown HTML ends the HTML block and lets markdown (e.g. "## ...") leak out.
    text = re.sub(r"(^|\s)#{1,6}(?=\s)", " ", str(text))
    return " ".join(text.split())


def host_of(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]


def safe_href(url: str) -> str:
    return esc(url) if re.match(r"^https?://", url or "") else "#"


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


def score_html(score: str) -> str:
    value = max(0.0, min(10.0, float(score)))
    tone, word = ("good", "Strong report") if value >= 8 else (
        ("mid", "Solid, with gaps") if value >= 6 else ("low", "Needs work")
    )
    return (
        f'<div class="score-wrap">'
        f'<div class="ring {tone}" style="--v:{value * 10:.0f}" aria-label="Critic score {value:g} out of 10">'
        f"<div><span>{value:g}<small>/ 10</small></span></div></div>"
        f'<div class="score-copy"><b>{word}</b><span>Scored by the critic agent</span></div>'
        f"</div>"
    )


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "report"


def pick_example() -> None:
    choice = st.session_state.get("example_pick")
    if choice:
        st.session_state["topic"] = choice


def missing_keys() -> list[str]:
    return [k for k in REQUIRED_KEYS if not os.getenv(k)]


@st.cache_data(ttl=300, show_spinner=False)
def openai_key_status(key: str) -> tuple[str, str]:
    """Free check (lists models) so a revoked key is caught before a run starts."""
    try:
        r = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=8,
        )
    except requests.RequestException:
        return "warn", "unreachable"
    if r.status_code == 200:
        return "ok", "valid"
    if r.status_code == 401:
        return "bad", "invalid"
    return "warn", f"HTTP {r.status_code}"


def key_status(name: str) -> tuple[str, str]:
    value = os.getenv(name)
    if not value:
        return "bad", "missing"
    if name == "OPENAI_API_KEY":
        return openai_key_status(value)
    return "ok", "set"


def explain_error(exc: Exception) -> tuple[str, str]:
    """Turn provider exceptions into a headline plus a concrete fix."""
    if isinstance(exc, openai.AuthenticationError):
        return (
            "OpenAI rejected your API key (401).",
            "The <code>OPENAI_API_KEY</code> in <code>.env</code> has been revoked, deleted or mistyped. "
            'Create a new key at <a href="https://platform.openai.com/api-keys" target="_blank">'
            "platform.openai.com/api-keys</a>, paste it into <code>.env</code>, then restart the app.",
        )
    if isinstance(exc, openai.RateLimitError):
        return (
            "OpenAI rate limit or quota exceeded.",
            "Check billing and usage limits on your OpenAI account, then try again.",
        )
    if isinstance(exc, openai.APIConnectionError):
        return "Could not reach OpenAI.", "Check your internet connection or proxy settings."
    if isinstance(exc, (InvalidAPIKeyError, MissingAPIKeyError)):
        return (
            "Tavily rejected your API key.",
            'Check <code>TAVILY_API_KEY</code> in <code>.env</code> (get one at '
            '<a href="https://app.tavily.com" target="_blank">app.tavily.com</a>), then restart the app.',
        )
    if isinstance(exc, UsageLimitExceededError):
        return "Tavily usage limit reached.", "Upgrade your Tavily plan or wait for the quota to reset."
    return "The research run failed.", esc(exc)


def show_error(title: str, hint: str) -> None:
    st.markdown(f'<div class="err" role="alert"><b>{title}</b><p>{hint}</p></div>', unsafe_allow_html=True)


def run_pipeline(topic: str, tracker_slot, status) -> dict:
    """Same four steps as pipeline.py, with progress shown in the UI."""
    state = {}

    def show(done, active=None):
        tracker_slot.markdown(tracker_html(done, active), unsafe_allow_html=True)
        if active is not None:
            name, desc, icon = STEPS[active]
            status.update(label=f"{icon} {name}: {desc}…", state="running")

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
    status.write(f"🌐 Found {len(state['sources'])} source(s).")

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
    status.write(f"📄 Read {host_of(state['scraped_url']) if state['scraped_url'] else 'the top source'} in depth.")

    # Step 3 - Writer
    show(2, 2)
    research_combined = (
        f"SEARCH RESULTS:\n{state['search_res']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scrape_res']}"
    )
    state["report"] = report_chain.invoke({"topic": topic, "research": research_combined})
    status.write("✍️ Drafted the report.")

    # Step 4 - Critic
    show(3, 3)
    state["critic"] = critic_chain.invoke({"report": state["report"]})
    status.write("🧐 Review complete.")

    show(4, None)
    return state


# ----------------------------------------------------------------- sidebar
key_states = {k: key_status(k) for k in REQUIRED_KEYS}
blocked = [k for k, (tone, _) in key_states.items() if tone == "bad"]

with st.sidebar:
    st.markdown(
        """
<div class="brand">
  <div class="logo" aria-hidden="true">🔎</div>
  <div><div class="name">AgentScholar</div><div class="tag">Multi-agent AI researcher</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.pills(
        "Try an example",
        EXAMPLES,
        selection_mode="single",
        key="example_pick",
        on_change=pick_example,
    )

    st.markdown('<div class="side-label">Agent pipeline</div>', unsafe_allow_html=True)
    st.markdown(
        '<ol class="flow">'
        + "".join(
            f'<li><span class="ix">{i}</span><div><b>{name}</b><div class="sub">{desc}</div></div></li>'
            for i, (name, desc, _) in enumerate(STEPS, start=1)
        )
        + "</ol>",
        unsafe_allow_html=True,
    )
    st.caption("A run usually takes one to three minutes.")

    st.markdown('<div class="side-label">API keys</div>', unsafe_allow_html=True)
    st.markdown(
        "".join(
            f'<div class="health {tone}"><span class="pip" aria-hidden="true"></span>'
            f'<code>{k}</code><span class="st">{label}</span></div>'
            for k, (tone, label) in key_states.items()
        ),
        unsafe_allow_html=True,
    )
    if st.button("Re-check keys", icon=":material/refresh:", width="stretch"):
        openai_key_status.clear()
        st.rerun()

# -------------------------------------------------------------------- hero
st.markdown(
    """
<div class="hero">
    <div class="eyebrow"><span class="live"></span>Multi-agent research engine</div>
    <h1>Deep research,<br/><span class="grad">done by a team of AI agents.</span></h1>
    <p>Enter any topic. Four specialised agents search the live web, read the best source, write a structured report and peer-review it.</p>
    <div class="chips">
        <span class="chip"><b>4</b> agents</span>
        <span class="chip"><b>Live</b> web search</span>
        <span class="chip"><b>Cited</b> sources</span>
        <span class="chip"><b>Scored</b> by a critic</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.form("research_form", border=False, enter_to_submit=True):
    col_input, col_btn = st.columns([5, 1.35], vertical_alignment="center")
    with col_input:
        topic = st.text_input(
            "Research topic",
            key="topic",
            placeholder="What do you want to research?  e.g. Solid-state batteries in EVs",
            label_visibility="collapsed",
            max_chars=200,
        )
    with col_btn:
        run = st.form_submit_button(
            "Research",
            type="primary",
            icon=":material/auto_awesome:",
            width="stretch",
        )

if blocked:
    show_error(
        "Can't run yet: " + ", ".join(f"{k} is {key_states[k][1]}" for k in blocked) + ".",
        "Fix the key in your <code>.env</code> file, restart the app, then press <b>Re-check keys</b>. "
        "New OpenAI keys: "
        '<a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com/api-keys</a>.',
    )

# --------------------------------------------------------------------- run
if run:
    topic = topic.strip()
    if not topic:
        st.toast("Enter a topic to research.", icon=":material/edit:")
    elif blocked:
        st.toast("Fix the API keys first.", icon=":material/key:")
    else:
        tracker_slot = st.empty()
        started = time.time()
        with st.status("Starting research…", expanded=False) as status:
            try:
                state = run_pipeline(topic, tracker_slot, status)
                elapsed = time.time() - started
                st.session_state["result"] = {"topic": topic, "state": state, "seconds": elapsed}
                status.update(label=f"Research complete in {elapsed:.0f}s", state="complete")
                st.toast("Your report is ready.", icon=":material/task_alt:")
            except Exception as exc:
                tracker_slot.empty()
                st.session_state.pop("result", None)
                openai_key_status.clear()
                title, hint = explain_error(exc)
                status.update(label=title, state="error", expanded=False)
                show_error(title, hint)

# ----------------------------------------------------------------- results
saved = st.session_state.get("result")

if saved:
    state = saved["state"]
    report = str(state.get("report", ""))
    score, critic_body = split_critic(str(state.get("critic", "")))
    sources = state.get("sources", [])

    st.markdown(
        f'<div class="meta"><span class="tag">Complete</span>Report on <b>{esc(saved["topic"])}</b></div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Critic score", f"{score}/10" if score else "—")
    m2.metric("Sources found", len(sources))
    m3.metric("Words", f"{len(report.split()):,}")
    m4.metric("Run time", f"{saved['seconds']:.0f}s")

    tab_report, tab_critic, tab_sources, tab_scrape = st.tabs(
        [
            ":material/article: Report",
            ":material/rate_review: Critic review",
            f":material/link: Sources ({len(sources)})",
            ":material/description: Scraped page",
        ]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(report)
        _, dl_col = st.columns([4, 1.4])
        with dl_col:
            st.download_button(
                "Download .md",
                data=report,
                file_name=f"{slugify(saved['topic'])}.md",
                mime="text/markdown",
                icon=":material/download:",
                width="stretch",
            )

    with tab_critic:
        with st.container(border=True):
            if score:
                st.markdown(score_html(score), unsafe_allow_html=True)
            st.markdown(critic_body)

    with tab_sources:
        if sources:
            # Leading <div> makes markdown treat this as a raw HTML block instead of wrapping it in <p>.
            st.markdown(
                '<div class="sources">'
                + "".join(
                    f'<a class="source" href="{safe_href(s["url"])}" target="_blank" rel="noopener noreferrer">'
                    f'<span class="num">{i}</span><span class="title">{esc(one_line(s["title"]))}</span>'
                    f'<div class="host">{esc(host_of(s["url"]))} ↗</div>'
                    f'<div class="snip">{esc(one_line(s["content"]))}</div></a>'
                    for i, s in enumerate(sources, start=1)
                )
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                st.markdown(str(state.get("search_res", "")))

    with tab_scrape:
        if state.get("scraped_url"):
            st.markdown(f"Page read by the reader agent: [{state['scraped_url']}]({state['scraped_url']})")
        with st.container(border=True):
            st.text(str(state.get("scrape_res", "")))

elif not run:
    st.markdown(
        """
<div class="empty">
  <div class="features">
    <div class="feature"><div class="fi" aria-hidden="true">🌐</div><b>Live web research</b><span class="d">Tavily search pulls fresh, relevant sources in seconds.</span></div>
    <div class="feature"><div class="fi" aria-hidden="true">📑</div><b>Structured reports</b><span class="d">Introduction, key findings, conclusion and full citations.</span></div>
    <div class="feature"><div class="fi" aria-hidden="true">🧠</div><b>Built-in peer review</b><span class="d">A critic agent scores every draft and flags the gaps.</span></div>
  </div>
  <div class="empty-note">Type a topic above or pick an example from the sidebar to see the agents at work.</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
<div class="app-footer">
  <span>Built with LangChain · OpenAI · Tavily · Streamlit</span>
  <a href="{REPO_URL}" target="_blank" rel="noopener noreferrer">View source on GitHub ↗</a>
</div>
""",
    unsafe_allow_html=True,
)
