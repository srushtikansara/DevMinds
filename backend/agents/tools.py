from tavily import TavilyClient
from app.config import settings

tavily_client = TavilyClient(api_key=settings.tavily_api_key)

def research_company_web(company_name:str) -> dict:
    response = tavily_client.search(
        query= f"What does {company_name} do? Recent news." ,
        max_results = 3,
    )
    summary = "\n".join(r["content"][:300] for r in response.get("results",[]))
    sources = [r["url"] for r in response.get("results",[])]
    return{"summary":summary,"sources":sources}