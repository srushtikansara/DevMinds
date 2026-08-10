import json
from datetime import datetime, timezone
from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperProfile, Session, Skill, Memory


@celery_app.task(name="update_developer_profile", bind=True, max_retries=3, default_retry_delay=10)
def update_developer_profile(self, user_id: str):
    db = SessionLocal()
    try:
        total_skills_tracked = db.query(Skill).filter(Skill.user_id == user_id).count()
        skills = (
            db.query(Skill)
            .filter(Skill.user_id == user_id)
            .order_by(Skill.proficiency_score.desc())
            .limit(20)
            .all()
        )
        skill_summary = [
            {
                "skill_name": s.skill_name,
                "proficiency_score": round(s.proficiency_score, 3),
                "signal_count": s.signal_count,
            }
            for s in skills
        ]

        top_memories = (
            db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(Memory.updated_at.desc())
            .limit(10)
            .all()
        )

        recent_highlights = [
            {"content": m.content[:200], "importance_score": round(m.importance_score, 3)}
            for m in top_memories
        ]

        sessions = db.query(Session).filter(Session.user_id == user_id).all()
        connector_counts = {}
        for s in sessions:
            connector_counts[s.connector_id] = connector_counts.get(s.connector_id, 0) + 1

        activity_summary = {
            "total_sessions": len(sessions),
            "total_memories": db.query(Memory).filter(Memory.user_id == user_id).count(),
            "total_skills_tracked": total_skills_tracked,
            "recent_highlights": recent_highlights,
        }
        
        profile = db.query(DeveloperProfile).filter(DeveloperProfile.user_id == user_id).first()
        if profile is None:
            profile = DeveloperProfile(
                user_id=user_id,
                skill_summary=skill_summary,
                activity_summary=activity_summary,
                version=1,
                last_computed_at=datetime.now(timezone.utc),
            )
            db.add(profile)
        else:
            profile.skill_summary = skill_summary
            profile.activity_summary = activity_summary
            profile.version += 1
            profile.last_computed_at = datetime.now(timezone.utc)

        db.commit()
        return {"skills_tracked": total_skills_tracked, "memories": activity_summary["total_memories"]}

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()