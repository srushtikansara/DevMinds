from mcp.server.fastmcp import FastMCP
import requests
import sys

sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")
from app.config import settings
mcp = FastMCP("DevMind")

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": f"Bearer {settings.devmind_api_key}"}

@mcp.tool()
def get_developer_profile() -> dict:
    """Get the user's current developer profile: tracked skills and recent activity highlights."""
    response = requests.get(f"{API_URL}/profile", headers=HEADERS)
    return response.json()

@mcp.tool()
def search_memories(query:str) -> dict:
    """Search the developer's memory for past solution to a described problem."""
    response = requests.get(f"{API_URL}/memories/search",params={"q":query},headers=HEADERS)
    return response.json()

@mcp.tool()
def get_recommendations() -> dict:
    """Get personalized recommendations for what the developer should learn next."""
    response = requests.get(f"{API_URL}/recommendations", headers=HEADERS)
    return response.json()

@mcp.tool()
def get_career_matches() -> dict:
    """Get the user's current job/internship recommendations from real job postings, ranked by fit_score."""
    response = requests.get(f"{API_URL}/career/matches",headers=HEADERS)
    return response.json()

@mcp.tool()
def get_learning_coaching(skill_name: str) -> dict:
    """Get a mentorship-style learning plan for a specific skill, based on the developer's real tracked work, related memories, and current job market demand."""
    response = requests.post(f"{API_URL}/learning/coach/{skill_name}", headers=HEADERS)
    task_id = response.json()["task_id"]

    import time
    for _ in range(15):  # poll for up to ~15 seconds
        time.sleep(1)
        result_response = requests.get(f"{API_URL}/learning/coach/result/{task_id}", headers=HEADERS)
        result_data = result_response.json()
        if result_data["status"] == "complete":
            return result_data["result"]

    return {"status": "still processing, try asking again in a few seconds"}

if __name__=="__main__":
    mcp.run()