import requests
from app.config import settings

ACTOR_ID = "worldunboxer~rapid-linkedin-scraper"


def search_jobs(job_titles: list[str], location: str = "India", limit: int = 10) -> list[dict]:
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": settings.apify_api_token}
    payload = {
        "jobs_titles": job_titles,
        "location": location,
        "jobs_entries": limit,
        "employment_type": "Internship",
        "experience": "Intern",
    }

    response = requests.post(url, params=params, json=payload)
    response.raise_for_status()
    raw_jobs = response.json()

    normalized = []
    for job in raw_jobs:
        normalized.append({
            "external_id": job.get("job_id", ""),
            "title": job.get("job_title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("location", ""),
            "description": job.get("job_description", ""),
            "url": job.get("apply_url", job.get("job_url", "")),
        })
    return normalized