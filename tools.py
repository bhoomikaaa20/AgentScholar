from dotenv import load_dotenv
load_dotenv()

import os
from langchain.tools import tool
from tavily import TavilyClient
from rich import print

tavily=TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
@tool
def web_search(query:str)->str:
    """Give the most relevant and reliable information regarding the topic given.Give title,url,content in it"""
    res=tavily.search(
        query=query,
        max_results=3
    )

    output=[]

    for result in res["results"]:
        output.append(
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Content: {result['content'][:200]}\n"
        )

    return "\n---\n".join(output)
    

print(web_search.invoke("what is ml"))

