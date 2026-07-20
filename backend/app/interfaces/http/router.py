from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.infrastructure.db.session import get_db
from app.infrastructure.db.models import Session as SessionModel, Connector, User , Memory
from app.infrastructure.embeddings.gemini_embeddings import get_embedding 
from app.infrastructure.vectorstore.chroma_client import find_similar
from workers.parser_worker import parse_session

router = APIRouter()
RAW_SESSIONS_DIR = "raw_sessions"
os.makedirs(RAW_SESSIONS_DIR, exist_ok=True)

VALID_TOOL_TYPES = {"claude_code", "cursor", "codex","antigravity"}


class SessionUploadRequest(BaseModel):
    session_upload_id: str
    tool_type: str
    started_at: datetime
    payload: dict


@router.post("/sessions", status_code=202)
def upload_session(body: SessionUploadRequest, db: DBSession = Depends(get_db)):

    if body.tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(400, f"tool_type must be one of {sorted(VALID_TOOL_TYPES)}")

    existing = (
        db.query(SessionModel)
        .filter(SessionModel.session_upload_id == body.session_upload_id)
        .first()
    )
    if existing:
        return {"session_id": existing.id, "status": existing.status}

    user = db.query(User).first()
    if user is None:
        raise HTTPException(500, "No user exists yet - create a dev user first")

    connector = (
        db.query(Connector)
        .filter(Connector.user_id == user.id, Connector.tool_type == body.tool_type)
        .first()
    )
    if connector is None:
        connector = Connector(user_id=user.id, tool_type=body.tool_type, status="active")
        db.add(connector)
        db.flush()

    try:
        raw_path = os.path.join(RAW_SESSIONS_DIR,f"{body.session_upload_id}.json")
        with open(raw_path,"w") as f:
            json.dump(body.payload,f)
            
        session = SessionModel(
            user_id=user.id,
            connector_id=connector.id,
            session_upload_id=body.session_upload_id,
            status="queued",
            started_at=body.started_at,
            raw_storage_uri=raw_path,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        parse_session.delay(session.id)
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(SessionModel)
            .filter(SessionModel.session_upload_id == body.session_upload_id)
            .first()
        )
        return {"session_id": existing.id, "status": existing.status}

    return {"session_id": session.id, "status": "queued"}

@router.get("/memories/search")
def search_name(q:str ,db: DBSession = Depends(get_db)):
    if not q or not q.strip():
        raise HTTPException(400,"Query cannot be empty")
    if len(q) > 500:
        raise HTTPException(422,"Query too long (500 max characters)")
    
    query_vector = get_embedding(q,task_type = "RETRIEVAL_QUERY")
    
    matches=find_similar(query_vector, top_k=5)
    
    results = []
    
    for match in matches:
        memory = db.query(Memory).filter(Memory.id == match["memory_id"]).first()
        if memory is None:
            continue
        
        similarity = 1 - match["distance"]
        results.append({
                "memory_id":memory.id,
                 "content": memory.content,
                "importance_score": memory.importance_score,
                "similarity": round(similarity, 3),
            })
        results.sort(key = lambda r: (r["similarity"]*0.7 + r["importance_score"] *0.3),reverse=True)
        return {"query": q, "results": results}