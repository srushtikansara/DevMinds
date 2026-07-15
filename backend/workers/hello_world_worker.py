from app.infrastructure.queue.celery_app import celery_app


@celery_app.task(name="hello_world")
def hello_world(message: str) -> str:
    return f"Celery worker received: {message}"