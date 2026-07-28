from app.infrastructure.queue.celery_app import celery_app
from agents.career_agent import build_career_agent
from agents.learning_agent import build_learning_agent


@celery_app.task(name="run_career_agent", bind=True, max_retries=3, default_retry_delay=10)
def run_career_agent(self, recommendation_id: str, user_id: str):
    agent = build_career_agent()
    result = agent.invoke({
        "recommendation_id": recommendation_id,
        "user_id": user_id,
        "decision_log": [],
    })
    return {
        "decision_log": result["decision_log"],
        "tailored_summary": result.get("tailored_summary"),
    }


@celery_app.task(name="run_learning_agent", bind=True, max_retries=3, default_retry_delay=10)
def run_learning_agent(self, user_id: str, skill_name: str):
    agent = build_learning_agent()
    result = agent.invoke({
        "user_id": user_id,
        "skill_name": skill_name,
        "decision_log": [],
    })
    return {
        "decision_log": result["decision_log"],
        "learning_plan": result.get("learning_plan"),
        "job_market_count": result.get("job_market_count"),
    }