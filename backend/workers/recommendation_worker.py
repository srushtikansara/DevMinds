from datetime import datetime, timezone

from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Skill, Recommendation
from app.infrastructure.llm.gemini_provider import recommend_next_skills
from workers.agent_worker import run_learning_agent


@celery_app.task(name="generate_recommendation", bind=True, max_retries=3, default_retry_delay=10)
def generate_recommendation(self, user_id: str):
    db = SessionLocal()
    try:
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        established_skills = [s for s in skills if s.signal_count >= 2]

        if not established_skills:
            return 0

        skill_summary = [
            {"skill_name": s.skill_name, "proficiency_score": s.proficiency_score, "signal_count": s.signal_count}
            for s in established_skills
        ]

        raw_recommendations = recommend_next_skills(skill_summary)
        raw_recommendations = recommend_next_skills(skill_summary)
    
        created_counts = 0
        for rec in raw_recommendations:
            skill_name = rec.get("skill_name")
            reason = rec.get("reason")

            if not skill_name or not reason:
                continue

            existing = (
                db.query(Recommendation)
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.type == "new_technology",
                    Recommendation.content == skill_name,
                )
                .first()
            )

            if existing:
                continue

            recommendation = Recommendation(
                user_id=user_id,
                type="new_technology",
                content=skill_name,
                relevance_score=float(rec.get("relevance_score", 0.5)),
                actioned=False,
                created_at=datetime.now(timezone.utc),
            )
            db.add(recommendation)
            created_counts += 1

        db.commit()
                        
        if created_counts > 0:
            top_rec = (
                db.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .order_by(Recommendation.relevance_score.desc())
                .first()
            )
            if top_rec:
                run_learning_agent.delay(user_id, top_rec.content)
        return created_counts

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()