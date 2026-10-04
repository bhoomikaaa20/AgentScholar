from agents import (
    web_search_agent,
    url_scrape_agent,
    report_chain,
    critic_chain
)


def research_pipeline(topic: str) -> dict:

    state = {}

    # Step 1 - Search Agent
    print("\n" + "=" * 50)
    print("Step 1 - Search agent is working...")
    print("=" * 50)

    search_res = web_search_agent.invoke({
        "messages": [
            (
                "user",
                f"Find recent, reliable and detailed information about: {topic}"
            )
        ]
    })

    state["search_res"] = search_res["messages"][-1].content

    print("\nSearch Results:\n")
    print(state["search_res"])


    # Step 2 - Reader Agent
    print("\n" + "=" * 50)
    print("Step 2 - Reader agent is scraping top resources...")
    print("=" * 50)

    scrape_res = url_scrape_agent.invoke({
        "messages": [
            (
                "user",
                f"""Based on the following search results about '{topic}',
pick the most relevant URL and scrape it for deeper content.

Search Results:
{state["search_res"][:800]}"""
            )
        ]
    })

    state["scrape_res"] = scrape_res["messages"][-1].content

    print("\nScraped Content:\n")
    print(state["scrape_res"])


    # Step 3 - Writer
    print("\n" + "=" * 50)
    print("Step 3 - Writer is drafting the report...")
    print("=" * 50)

    research_combined = (
        f"SEARCH RESULTS:\n"
        f"{state['search_res']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n"
        f"{state['scrape_res']}"
    )

    state["report"] = report_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    print("\nFinal Report:\n")
    print(state["report"])


    # Step 4 - Critic
    print("\n" + "=" * 50)
    print("Step 4 - Critic is reviewing the report...")
    print("=" * 50)

    state["critic"] = critic_chain.invoke({
        "report": state["report"]
    })

    print("\nCritic Report:\n")
    print(state["critic"])


    return state


if __name__ == "__main__":

    topic = input("\nEnter a research topic: ")

    research_pipeline(topic)