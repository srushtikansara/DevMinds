from celery import Celery

from app.config import settings

celery_app = Celery(
    "devmind",
    broker = settings.redis_url,
    backend = settings.redis_url,
    include = ["workers.hello_world_worker","workers.parser_worker"],
)

celery_app.conf.update(
    task_sterilizer ="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
)