from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Conversation, Session, DeveloperEvent
from app.infrastructure.llm.gemini_provider import extract_events
from workers.memory_worker import process_memory
from workers.skill_worker import process_skills
from workers.profile_worker import update_developer_profile
from workers.recommendation_worker import generate_recommendation

@celery_app.task(name="extract_events", bind=True, max_retries=3, default_retry_delay=10)
def extract_events_task(self, conversation_id: str):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")

        session = db.query(Session).filter(Session.id == conversation.session_id).first()
        if session is None:
            raise ValueError(f"Session {conversation.session_id} not found")

        turns = conversation.structured_content.get("turns", [])
        conversation_text = "\n\n".join(
            f"{turn['role']}: {turn['content']}" for turn in turns
        )

        if not conversation_text.strip():
            return 0

        raw_events = extract_events(conversation_text)

        created_events = []
        for event in raw_events:
            event_type = event.get("event_type")
            description = event.get("description")
            if not event_type or not description:
                continue

            db_event = DeveloperEvent(
                conversation_id=conversation.id,
                user_id=session.user_id,
                event_type=event_type,
                technology_tags=event.get("technology_tags", ""),
                confidence=float(event.get("confidence", 0.5)),
                description=description,
            )
            db.add(db_event)
            created_events.append(db_event)

        db.commit()

        for db_event in created_events:
            db.refresh(db_event)
            process_memory.delay(db_event.id)
            process_skills.delay(db_event.id)
            update_developer_profile.delay(session.user_id)
            generate_recommendation.delay(session.user_id)
        return len(created_events)

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()