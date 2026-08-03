import requests
import sys
import datetime

sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")
from app.config import settings

GITHUB_HEADERS = {"Authorization": f"Bearer {settings.github_token}"}
API_URL = "http://localhost:8000/api/v1"
DEVMIND_HEADERS = {"Authorization": f"Bearer {settings.devmind_api_key}"}

def fetch_recent_commits(username:str,since_date:str) -> list[dict]:
    response = requests.get(
        "https://api.github.com/search/commits",
        headers={**GITHUB_HEADERS, "Accept": "application/vnd.github.cloak-preview"},
        params={"q": f"author:{username} committer-date:>{since_date}"},
    )
    response.raise_for_status()
    return response.json().get("items", [])

def normalize_commit(commit_data: dict) -> dict:
    message = commit_data["commit"]["message"]
    repo_name = commit_data["repository"]["full_name"]
    sha = commit_data["sha"][:7]

    return {
        "role": "user",
        "text": f"[GitHub commit in {repo_name}] {message} (commit {sha})",
        "timestamp": commit_data["commit"]["author"]["date"],
    }
    
def upload_session(username: str, since_date: str):
    commits = fetch_recent_commits(username, since_date)
    if not commits:
        print(f"No new commits found since {since_date}")
        return

    normalized_turns = [normalize_commit(c) for c in commits]

    payload = {
        "session_upload_id": f"github-{username}-{since_date}",
        "connector_type": "github",
        "turns": normalized_turns,
    }

    response = requests.post(f"{API_URL}/sessions", json=payload, headers=DEVMIND_HEADERS)
    print(f"Parsed {len(commits)} real commits")
    print("Status:", response.status_code)
    print(response.json())
    
if __name__ == "__main__":
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    upload_session(username="srushtikansara", since_date=since_date)