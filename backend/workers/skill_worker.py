from datetime import datetime, timezone

from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperEvent, SkillSignal, Skill


@celery_app.task(name="process_skills", bind=True, max_retries=3, default_retry_delay=10)
def process_skills(self, developer_event_id: str):
    db = SessionLocal()
    try:
        event = db.query(DeveloperEvent).filter(DeveloperEvent.id == developer_event_id).first()
        if event is None:
            raise ValueError(f"DeveloperEvent {developer_event_id} not found")

        raw_tags = event.technology_tags or ""
        skill_names = [tag.strip().lower() for tag in raw_tags.split(",") if tag.strip()]

        if not skill_names:
            return 0

        updated_count = 0
        for skill_name in skill_names:
            # Record the raw signal first - one row per event/skill pairing
            signal = SkillSignal(
                developer_event_id=event.id,
                skill_name=skill_name,
                weight=1.0,
            )
            db.add(signal)

            # Then update the rolled-up Skill score
            skill = (
                db.query(Skill)
                .filter(Skill.user_id == event.user_id, Skill.skill_name == skill_name)
                .first()
            )
            if skill is None:
                skill = Skill(
                    user_id=event.user_id,
                    skill_name=skill_name,
                    proficiency_score=0.1,
                    signal_count=1,
                    last_updated=datetime.now(timezone.utc),
                )
                db.add(skill)
            else:
                skill.signal_count += 1
                skill.proficiency_score = min(
                    1.0, skill.proficiency_score + (0.1 * (1 - skill.proficiency_score))
                )
                skill.last_updated = datetime.now(timezone.utc)

            updated_count += 1

        db.commit()
        return updated_count

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()