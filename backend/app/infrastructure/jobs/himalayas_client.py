import re
import requests

BASE_URL = "https://himalayas.app/jobs/api/search"

def strip_html(text:str) -> str:
    """Remove HTML tags, leaving plain readable text."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



def search_jobs(keywords: str, limit: int = 10) -> list[dict]:
    params = {"keywords": keywords, "limit": limit}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    raw_jobs = data.get("jobs", [])

    normalized = []
    for job in raw_jobs:
        locations = job.get("locationRestrictions", [])
        normalized.append({
            "external_id": job.get("guid", ""),
            "title": job.get("title", ""),
            "company": job.get("companyName", ""),
            "location": ", ".join(locations) if locations else "Remote (worldwide)",
            "description": job.get("description", ""),
            "url": job.get("applicationLink", ""),
        })
    return normalized