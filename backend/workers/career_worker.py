from datetime import datetime, timezone
import time
from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperProfile, JobPosting, CareerRecommendation
from app.infrastructure.jobs.apify_linkedin_client import search_jobs
from app.infrastructure.llm.gemini_provider import score_job_fit


@celery_app.task(name="find_job_matches", bind=True, max_retries=3, default_retry_delay=10)
def find_job_matches(self, user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(DeveloperProfile).filter(DeveloperProfile.user_id == user_id).first()
        if profile is None:
            return 0

        job_titles = ["Data Scientist Intern", "Machine Learning Engineer Intern", "Business Analyst Intern"]
        raw_jobs = search_jobs(job_titles)
        time.sleep(13)

        created_count = 0
        for job in raw_jobs:
            posting = db.query(JobPosting).filter(JobPosting.external_id == job["external_id"]).first()

            if posting is None:
                posting = JobPosting(
                    external_id=job["external_id"],
                    title=job["title"],
                    company=job["company"],
                    location=job["location"],
                    description=job["description"],
                    url=job["url"],
                    source="linkedin",
                )
                db.add(posting)
                db.flush()

            existing_rec = (
                db.query(CareerRecommendation)
                .filter(
                    CareerRecommendation.user_id == user_id,
                    CareerRecommendation.job_postings_id == posting.id,
                )
                .first()
            )
            if existing_rec:
                continue

            fit = score_job_fit(profile.skill_summary, posting.description)

            recommendation = CareerRecommendation(
                user_id=user_id,
                job_postings_id=posting.id,
                fit_score=fit["fit_score"],
                fit_reason=fit["reason"],
                reviewed=False,
            )
            db.add(recommendation)
            created_count += 1

        db.commit()
        return created_count

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()