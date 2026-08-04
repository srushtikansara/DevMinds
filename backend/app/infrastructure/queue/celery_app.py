from celery import Celery

from app.config import settings

celery_app = Celery(
    "devmind",
    broker = settings.redis_url,
    backend = settings.redis_url,
    include = ["workers.hello_world_worker","workers.parser_worker","workers.event_extractor_worker","workers.memory_worker", "workers.skill_worker","workers.profile_worker","workers.recommendation_worker","workers.report_worker","workers.resume_worker","workers.career_worker","workers.agent_worker","workers.workflow_worker"],
)

celery_app.conf.update(
    task_serializer ="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
)