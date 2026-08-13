from datetime import datetime, timezone, timedelta
from app.infrastructure.slack.slack_client import post_message
from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Memory, Skill, Recommendation, WeeklyReport, DeveloperEvent, SkillEvent
from app.infrastructure.llm.gemini_provider import client
from pydantic import BaseModel

class LearningPatternAnalysis(BaseModel):
    pattern: str
    how_to_learn: str
    
def analyze_learning_patterns(db, user_id: str) -> str | None:
    events = (
        db.query(DeveloperEvent.description, Skill.skill_name)
        .join(SkillEvent, SkillEvent.developer_event_id == DeveloperEvent.id)
        .join(Skill, Skill.id == SkillEvent.skill_id)
        .filter(Skill.user_id == user_id)
        .order_by(DeveloperEvent.occurred_at.desc())
        .limit(50)
        .all()
    )
    if len(events) < 15:
        return None

    events_text = "\n".join(f"[{skill}] {desc}" for desc, skill in events)
    prompt = f"""Here are a developer's real, tracked activity events across multiple skills:

{events_text}

Do two things, based ONLY on real evidence in these events:

1. Describe, in one clear sentence, a genuine, consistent pattern in HOW this
developer approaches learning/problem-solving - or say "No consistent pattern -
approach varies by domain" if it genuinely varies.

2. Give ONE concrete, actionable sentence of advice on how this developer should
approach learning a NEW skill, given their demonstrated real style. Be specific
and practical, not generic.

"""
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": LearningPatternAnalysis,
        }
    )
    result: LearningPatternAnalysis = response.parsed
    return {"pattern": result.pattern, "how_to_learn": result.how_to_learn}
    
@celery_app.task(name="generate_weekly_report", bind=True, max_retries=3, default_retry_delay=10)
def generate_weekly_report(self, user_id: str, target_week_start: str | None = None):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        if target_week_start:
            week_start_date = datetime.strptime(target_week_start, "%Y-%m-%d").date()
        else:
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
            .join(SkillEvent, SkillEvent.skill_id == Skill.id)
            .join(DeveloperEvent, DeveloperEvent.id == SkillEvent.developer_event_id)
            .filter(Skill.user_id == user_id, DeveloperEvent.occurred_at >= week_start_dt)
            .distinct()
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

        learning_analysis = analyze_learning_patterns(db, user_id)
        summary_json["learning_pattern"] = learning_analysis["pattern"] if learning_analysis else None
        summary_json["how_to_learn"] = learning_analysis["how_to_learn"] if learning_analysis else None

        report = (
            db.query(WeeklyReport)
            .filter(WeeklyReport.user_id == user_id, WeeklyReport.week_start == week_start_date)
            .first()
        )
        if report is None:
            report = WeeklyReport(user_id=user_id, week_start=week_start_date, summary_json=summary_json, generated_at=now)
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
    
