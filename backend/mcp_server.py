from mcp.server.fastmcp import FastMCP
import requests
import sys
import time

sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")
from app.config import settings
mcp = FastMCP("DevMind")

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": f"Bearer {settings.devmind_api_key}"}
TIMEOUT = 10  # seconds - fail fast instead of hanging forever


@mcp.tool()
def get_developer_profile() -> dict:
    """Get the user's current developer profile: tracked skills and recent activity highlights and learning patterns."""
    profile_response = requests.get(f"{API_URL}/profile", headers=HEADERS, timeout=TIMEOUT)
    pattern_response = requests.get(f"{API_URL}/profile/learning-pattern", headers=HEADERS, timeout=TIMEOUT)
    data = profile_response.json()
    data["learning_pattern"] = pattern_response.json()
    return data


@mcp.tool()
def search_memories(query: str) -> dict:
    """Search the developer's memory for past solution to a described problem."""
    response = requests.get(f"{API_URL}/memories/search", params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def get_recommendations() -> dict:
    """Get personalized recommendations for what the developer should learn next."""
    response = requests.get(f"{API_URL}/recommendations", headers=HEADERS, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def get_career_matches() -> dict:
    """Get the user's current job/internship recommendations from real job postings, ranked by fit_score."""
    response = requests.get(f"{API_URL}/career/matches", headers=HEADERS, timeout=TIMEOUT)
    return response.json()


@mcp.tool()
def get_learning_coaching(skill_name: str, relearn: bool = False) -> dict:
    """Get a mentorship-style learning plan for a specific skill, based on the developer's real tracked work, related memories, and current job market demand. Set relearn=True to get a cross-tool summary of what you've already learned about this skill, instead of a beginner/next-steps plan."""
    try:
        response = requests.post(
            f"{API_URL}/learning/coach/{skill_name}",
            params={"relearn": relearn},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        task_id = response.json()["task_id"]
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Failed to queue task: {e}"}

    for _ in range(40):
        time.sleep(1)
        try:
            result_response = requests.get(f"{API_URL}/learning/coach/result/{task_id}", headers=HEADERS, timeout=TIMEOUT)
            result_data = result_response.json()
            if result_data.get("status") == "complete":
                return result_data["result"]
        except requests.exceptions.RequestException:
            continue

    return {"status": "still processing, try asking again in a few seconds", "task_id": task_id}

@mcp.tool()
def draft_email(to:str,subject:str,body:str)-> dict:
    """Draft an email in Gmail (never sends automatically - user reviews and sends manually)."""
    try:
        response = requests.post(f"{API_URL}/office/draft-email", json={"to": to, "subject": subject, "body": body}, headers=HEADERS, timeout=TIMEOUT)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
def log_to_notion(title:str,content:str) ->dict:
    """Create a new page in the connected Notion database with a title and content."""
    try:
        response = requests.post(f"{API_URL}/office/notion-log", json={"title": title, "content": content}, headers=HEADERS, timeout=TIMEOUT)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    


if __name__ == "__main__":
    mcp.run()