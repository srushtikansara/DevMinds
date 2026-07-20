from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.infrastructure.db.session import get_db
from app.infrastructure.db.models import Session as SessionModel, Connector, User

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