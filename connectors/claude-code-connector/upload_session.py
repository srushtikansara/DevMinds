import sys
sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
import requests
from app.config import settings

API_URL = "http://localhost:8000/api/v1/sessions"
def parse_claude_code_jsonl(filepath: str) -> list[dict]:
    """Read a real Claude Code .jsonl file and extract only real conversation turns."""
    turns = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)

            if entry.get("type") not in ("user", "assistant"):
                continue

            message = entry.get("message", {})
            role = message.get("role")
            content = message.get("content")

            if role is None or content is None:
                continue

            if isinstance(content, list):
                text_parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                content = "\n".join(text_parts)

            if content:
                turns.append({"role": role, "content": content})

    return turns

def upload_session(filepath:str, session_id:str) :
    headers = {"Authorization": f"Bearer {settings.devmind_api_key}"}
    turns = parse_claude_code_jsonl(filepath)
    print(f"Parsed {len(turns)} real conversations with {filepath}")
    
    payload = {
        "session_upload_id":f"claude_code-{session_id}",
        "tool_type":"claude_code",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"turns":turns},
    }
    
    response = requests.post(API_URL,json=payload,headers=headers)
    print(f"Status: {response.status_code}")
    print(response.json())
    
if __name__== "__main__":
    
    if len(sys.argv) != 2:
        print("Usage: python upload_session.py <path-to-jsonl-file>")
        sys.exit(1)
        
    jsonl_path = sys.argv[1]
    session_id = Path(jsonl_path).stem  
    upload_session(jsonl_path, session_id)