from datetime import datetime, timezone, timedelta

from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Memory, Skill, Recommendation, WeeklyReport


@celery_app.task(name="generate_weekly_report", bind=True, max_retries=3, default_retry_delay=10)
def generate_weekly_report(self, user_id: str):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        week_start_date = (now - timedelta(days=now.weekday())).date()
        week_start_dt = datetime.combine(week_start_date, datetime.min.time(), tzinfo=timezone.utc)

        week_memories = (
            db.query(Memory)
            .filter(Memory.user_id == user_id, Memory.updated_at >= week_start_dt)
            .order_by(Memory.importance_score.desc())
            .all()
        )

        week_skills = (
            db.query(Skill)
            .filter(Skill.user_id == user_id, Skill.last_updated >= week_start_dt)
            .order_by(Skill.proficiency_score.desc())
            .all()
        )

        week_recommendation = (
            db.query(Recommendation)
            .filter(
                Recommendation.user_id == user_id,
                Recommendation.created_at >= week_start_dt,
                Recommendation.actioned == False,
            )
            .order_by(Recommendation.relevance_score.desc())
            .all()
        )

        summary_json = {
            "memories_this_week": [
                {"content": m.content[:200], "importance_score": round(m.importance_score, 3)}
                for m in week_memories
            ],
            "skills_active_this_week": [
                {"skill_name": s.skill_name, "proficiency_score": round(s.proficiency_score, 3)}
                for s in week_skills
            ],
            "open_recommendations": [
                {"content": r.content, "relevance_score": r.relevance_score}
                for r in week_recommendation
            ],
            "totals": {
                "memories": len(week_memories),
                "skills": len(week_skills),
                "recommendations": len(week_recommendation),
            },
        }

        report = (
            db.query(WeeklyReport)
            .filter(WeeklyReport.user_id == user_id, WeeklyReport.week_start == week_start_date)
            .first()
        )

        if report is None:
            report = WeeklyReport(
                user_id=user_id,
                week_start=week_start_date,
                summary_json=summary_json,
                generated_at=now,
            )
            db.add(report)
        else:
            report.summary_json = summary_json
            report.generated_at = now

        db.commit()
        return summary_json["totals"]

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()