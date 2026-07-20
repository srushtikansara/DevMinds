import sys
import re
import json
import requests
from pathlib import Path
from datetime import datetime,timezone

API_URL = "http://localhost:8000/api/v1/sessions"

def parse_antigravity_transcript(file_path:str) -> list[dict]:
    """Read a real Antigravity IDE transcript.jsonl and extract geniuine conversation turns"""
    turns=[]
    with open(file_path,"r",encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            
            entry_type= entry.get("type")
            
            content= entry.get("content","")
            
            if entry_type == "USER_INPUT":
                
                match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL)
                if match:
                    turns.append({"role":"user","content":match.group(1).strip()})
                    
            elif entry_type=="PLANNER_RESPONSE":
                
                if content:
                    turns.append({"role":"assistant","content":content})
                    
    return turns

def upload_session(file_path:str, session_id:str):
    turns = parse_antigravity_transcript(file_path)
    print(f"Parsed {len(turns)} real conversations turns from {file_path}")
    
    payload = {
        "session_upload_id":f"antigravity-{session_id}",
        "tool_type":"antigravity",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "payload":{"turns":turns},
    }
            
    response = requests.post(API_URL,json=payload)
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_session.py <path-to-transcript.jsonl>") 
        sys.exit(1)
    
    transcript_path= sys.argv[1]
    
    session_id = Path(transcript_path).parent.parent.parent.name
    upload_session(transcript_path, session_id)
            
        