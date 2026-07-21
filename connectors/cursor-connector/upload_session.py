import sys
sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")

import json
import sqlite3
import shutil
import requests
from pathlib import Path
from datetime import datetime,timezone

from app.config import settings


API_URL = "http://localhost:8000/api/v1/sessions"

TYPE_MAP = {1: "user", 2: "assistant"}

def parse_cursor_db(db_path:str) ->list[dict]:
    """Read a real cursor state.vscdb,extract every real conversation as a list of session."""
    copy_path = str(db_path) + "devmind_copy"
    shutil.copy2(db_path,copy_path)
    for suffix in ["-wal","shm"]:
        sibling = db_path + suffix
        if Path(sibling).exists():
            shutil.copy2(sibling, copy_path + suffix)
    
    conn = sqlite3.connect(copy_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT key,value FROM cursorDiskKV WHERE key LIKE 'composerData:%';")
    all_composer = cursor.fetchall()
    
    sessions=[]
    for key,value in all_composer:
        if value is None:
            continue  
        composer_id = key.split(":",1)[1]
        data = json.loads(value)
        headers = data.get("fullConversationHeadersOnly",[])
        
        if not headers:
            continue
        
        turns = []
        
        for header in headers:
            bubble_type = header.get("type")
            role = TYPE_MAP.get(bubble_type)
            if role is None:
                continue
            
            bubble_type=header.get("bubbleId")
            bubble_key=f"bubbleId:{composer_id}:{bubble_type}"
            cursor.execute("SELECT value FROM cursordiskKV WHERE key=?",(bubble_key,))
            bubble_row = cursor.fetchone()
            if bubble_row is None:
                continue
            
            bubble_data = json.loads(bubble_row[0])
            text=bubble_data.get("text","")
            if text:
                turns.append({"role":role,"content":text})
                
        if turns:
            sessions.append({"composer_id": composer_id, "turns": turns})
            
    conn.close()
    return sessions

def upload_session(composer_id: str, turns: list[dict]):
    headers = {"Authorization": f"Bearer {settings.devmind_api_key}"}
    payload = {
        "session_upload_id": f"cursor-{composer_id}",
        "tool_type": "cursor",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "payload": {"turns": turns},
    }

    response = requests.post(API_URL, json=payload,headers=headers)
    print(f"[{composer_id}] {len(turns)} turns - Status: {response.status_code}")
    print("Raw response text:", response.text[:1000])
    
if __name__ =="__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_session.py <path-to-state.vscdb>")
        sys.exit(1)

    db_path = sys.argv[1]
    sessions = parse_cursor_db(db_path)
    print(f"Found {len(sessions)} real conversation(s) in the database\n")

    for session in sessions:
        upload_session(session["composer_id"], session["turns"])        
            