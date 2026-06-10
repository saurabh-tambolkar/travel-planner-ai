from dotenv import load_dotenv
load_dotenv()
from tavily import TavilyClient
import os

api_key=os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=api_key)

def tavily_search(query: str) -> str:

    response = tavily_client.search(query=query,max_results=5)

    results = []
    for i,r in enumerate(response["results"],1):
        title = r.get("title", "N/A")
        url = r.get("url", "N/A")
        snippet = r.get("content", "N/A")[:300]
        results.append(f"{i}. Title: {title}\nURL: {url}\nSnippet: {snippet}\n")
    return "\n".join(results)