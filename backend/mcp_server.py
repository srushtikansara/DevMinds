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

if __name__=="__main__":
    mcp.run()