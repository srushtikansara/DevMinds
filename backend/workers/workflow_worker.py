from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import CareerRecommendation, JobPosting
from app.infrastructure.notion.notion_client import log_application
from app.infrastructure.gmail.gmail_client import create_followup_draft


@celery_app.task(name="workflow_high_fit_job_alert", bind=True, max_retries=3, default_retry_delay=10)
def workflow_high_fit_job_alert(self, user_id: str, fit_threshold: float = 0.7):
    """A 'saved workflow': automatically finds new, unreviewed, high-fit jobs
    and logs + drafts a follow-up for each - no manual /prepare call needed."""
    db = SessionLocal()
    try:
        high_fit_jobs = (
            db.query(CareerRecommendation, JobPosting)
            .join(JobPosting, CareerRecommendation.job_postings_id == JobPosting.id)
            .filter(
                CareerRecommendation.user_id == user_id,
                CareerRecommendation.reviewed == False,
                CareerRecommendation.fit_score >= fit_threshold,
            )
            .all()
        )

        processed_count = 0
        for rec, posting in high_fit_jobs:
            try:
                log_application(posting.title, posting.company, rec.fit_score, posting.description[:200])
            except Exception as e:
                print(f"Notion logging failed for {posting.title} (non-fatal): {e}")

            try:
                create_followup_draft(
                    to="recruiter@example.com",
                    subject=f"Interested in {posting.title} at {posting.company}",
                    body=f"Hi,\n\nI noticed the {posting.title} role and wanted to express my interest.\n\nBest regards",
                )
            except Exception as e:
                print(f"Gmail draft failed for {posting.title} (non-fatal): {e}")

            rec.reviewed = True
            processed_count += 1

        db.commit()
        return processed_count
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()