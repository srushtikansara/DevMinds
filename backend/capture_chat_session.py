import sys
sys.path.insert(0,r"C:\Users\Srushti\Desktop\DevMind\backend")
import requests
import uuid
from app.config import settings
from datetime import datetime,timezone

print("Paste your conversation summary(or key exchanges), then press Ctrl+Z, Enter (Windows):")
content = sys.stdin.read()

payload = {
    "session_upload_id": f"claude-chat-{uuid.uuid4().hex[:8]}",
    "tool_type": "claude_code", 
    "started_at": datetime.now(timezone.utc).isoformat(),
    "payload": {"turns": [{"role": "user", "content": content}]},
}

headers = {"Authorization": f"Bearer {settings.devmind_api_key}"}
response = requests.post("http://localhost:8000/api/v1/sessions", json=payload, headers=headers)
print(response.json())
