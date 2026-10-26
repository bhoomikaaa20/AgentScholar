from dotenv import load_dotenv
load_dotenv(override=True)  # .env wins over stale shell variables

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_agent
from tools import web_search, url_scrape
from langchain_core.prompts import ChatPromptTemplate


# Model
llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0
)


# Agent 1 - Web Search
web_search_agent = create_agent(
    model=llm,
    tools=[web_search]
)


# Agent 2 - URL Scraper
url_scrape_agent = create_agent(
    model=llm,
    tools=[url_scrape]
)


# Report Prompt
report_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research writer. Write clear, structured and insightful reports."
    ),
    (
        "human",
        """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""
    ),
])

report_chain = report_prompt | llm | StrOutputParser()


# Critic Prompt
critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a sharp and constructive research critic. Be honest and specific."
    ),
    (
        "human",
        """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser()