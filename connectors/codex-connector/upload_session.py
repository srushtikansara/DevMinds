import sys
import json
import requests
from pathlib import Path
from datetime import datetime,timezone

API_URL="http://localhost:8000/api/v1/sessions"

def parser_codex_jsonl(file_path: str) -> list[dict]:
    """Read a real Codex session .jsonl file and extract genuine conversation turns."""
    turns = []
    with open (file_path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            entry=json.loads(line)
            
            if entry.get("type") != "response_item":
                continue
            
            payload = entry.get("payload",{})
            
            if payload.get("type")!= "message":
                continue
            
            role = payload.get("role")
            
            if role == "developer":
                continue
            
            if role not in ("user","assistant"):
                continue
            
            content_blocks = payload.get("content",[])
            text_parts=[]
            for block in content_blocks:
                if not  isinstance(block,dict):
                    continue
                text = block.get("text","")
                
                if text.strip().startswith("<"):
                    continue
                
                if text:
                    text_parts.append(text)
            combined_text = "\n".join(text_parts)
            if combined_text:
                turns.append({"role": role, "content": combined_text})

    return turns

def upload_session(file_path:str , session_id:str):
    turns=parser_codex_jsonl(file_path)
    print(f"Parsed {len(turns)} real conversation turns from {file_path}")
    
    payload = {
        "session_upload_id": f"codex-{session_id}",
        "tool_type": "codex",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"turns": turns},
    }
    
    response = requests.post(API_URL,json=payload)
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_session.py <path-to-jsonl-file>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    session_id = Path(jsonl_path).stem  # e.g. "rollout-2026-07-10T12-25-39-019f4acf..."
    upload_session(jsonl_path, session_id)
    