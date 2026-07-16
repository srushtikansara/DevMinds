import json

from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Session, Conversation
from workers.event_extractor_worker import extract_events_task

@celery_app.task(name="parse_session", bind=True, max_retries=3, default_retry_delay=10)
def parse_session(self, session_id: str):

    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        with open(session.raw_storage_uri, "r") as f:
            raw_payload = json.load(f)

        turns = raw_payload.get("turns", [])
        structured_turns = []

        for turn in turns:
            structured_turns.append({
                "role": turn.get("role", "unknown"),
                "content": turn.get("content", ""),
            })

        # everything below is now OUTSIDE the for loop - runs once per session
        conversation = Conversation(
            session_id=session.id,
            turn_count=len(structured_turns),
            structured_content={"turns": structured_turns},
        )
        db.add(conversation)

        session.status = "parsed"

        db.commit()
        db.refresh(conversation)
        extract_events_task.delay(conversation.id)
        return conversation.id

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()