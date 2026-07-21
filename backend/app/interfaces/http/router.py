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
from app.infrastructure.db.models import DeveloperProfile,WeeklyReport
from app.interfaces.http.auth import get_current_user

from datetime import date
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
def upload_session(body: SessionUploadRequest, user: User = Depends(get_current_user) ,db: DBSession = Depends(get_db)):

    if body.tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(400, f"tool_type must be one of {sorted(VALID_TOOL_TYPES)}")

    existing = (
        db.query(SessionModel)
        .filter(SessionModel.session_upload_id == body.session_upload_id)
        .first()
    )
    if existing:
        return {"session_id": existing.id, "status": existing.status}

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
def search_name(q: str, user: User = Depends(get_current_user) ,db: DBSession = Depends(get_db)):
    if not q or not q.strip():
        raise HTTPException(400, "Query cannot be empty")
    if len(q) > 500:
        raise HTTPException(422, "Query too long (500 max characters)")

    query_vector = get_embedding(q, task_type="RETRIEVAL_QUERY")

    matches = find_similar(query_vector, top_k=10)

    results = []

    for match in matches:
        try:
            memory = db.query(Memory).filter(Memory.id == match["memory_id"]).first()
        except Exception:
            db.rollback()
            continue  

        if memory is None:
            continue

        similarity = 1 - match["distance"]
        results.append({
            "memory_id": memory.id,
            "content": memory.content,
            "importance_score": memory.importance_score,
            "similarity": round(similarity, 3),
        })

    results.sort(key=lambda r: (r["similarity"] * 0.7 + r["importance_score"] * 0.3), reverse=True)
    return {"query": q, "results": results}

@router.get("/profile")
def get_profile(user: User = Depends(get_current_user),db: DBSession = Depends(get_db)):
    profile = db.query(DeveloperProfile).filter(DeveloperProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(404, "Profile not yet computed - upload at least one session first")

    return {
        "user_id": profile.user_id,
        "skill_summary": profile.skill_summary,
        "activity_summary": profile.activity_summary,
        "last_computed_at": profile.last_computed_at,
    }
    
@router.get("/reports/{week_start}")
def get_weekly_report( week_start: date,user: User = Depends(get_current_user) , db: DBSession = Depends(get_db)):
   
    report= (
        db.query(WeeklyReport)
        .filter(WeeklyReport.user_id == user.id, WeeklyReport.week_start == week_start)
        .first()
    )
    
    if report is None:
        raise HTTPException(404, f"No report generated for week starting {week_start}")

    return {
        "week_start": report.week_start,
        "report_storage_uri": report.report_storage_uri,
        "summary_json": report.summary_json,
        "generated_at": report.generated_at,
    }