from dotenv import load_dotenv
load_dotenv()

import os
import requests
from langchain.tools import tool
from tavily import TavilyClient
from rich import print
from bs4 import BeautifulSoup


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


@tool
def url_scrape(url:str)->str:
    """Scrape a webpage and return its clean text content for deeper analysis."""
    try:
        response=requests.get(url,timeout=8,headers={"User-Agent": "Mozilla/5.0"})
        soup=BeautifulSoup(response.text,"html.parser")
        
        for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
        
        res=soup.get_text(separator=" ",strip=True)[:3000]
            
        return res

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"

    
            
            
        
