from datetime import datetime, timezone
from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperProfile, Resume
from app.infrastructure.llm.gemini_provider import generate_resume_content
from app.infrastructure.documents.resume_builder import build_resume_docx
from app.infrastructure.drive.drive_client import upload_resume_to_drive

@celery_app.task(name="generate_resume", bind=True, max_retries=3, default_retry_delay=10)
def generate_resume(self, user_id: str, personal_info: dict):
    db = SessionLocal()
    try:
        profile = db.query(DeveloperProfile).filter(DeveloperProfile.user_id == user_id).first()
        if profile is None:
            return None

        content = generate_resume_content(
            skill_summary=profile.skill_summary,
            recent_highlights=profile.activity_summary.get("recent_highlights", []),
            roles=personal_info["roles"],
            target_position=personal_info.get("target_position", ""),
            template_description=personal_info.get("template_description", ""),
        )
        content["contact_info"] = {
            "full_name": personal_info["full_name"],
            "email": personal_info["email"],
            "phone": personal_info["phone"],
            "linkedin_url": personal_info["linkedin_url"],
            "portfolio_url": personal_info["portfolio_url"],
        }
        content["education"] = personal_info["education"]
        content["certificates"] = personal_info.get("certificates", [])
        content["target_position"] = personal_info.get("target_position", "")

        resume = Resume(
            user_id=user_id,
            content_json=content,
            source="generated",
            version=1,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        file_path = build_resume_docx(content, resume.id, template=personal_info.get("template"))

        try:
            drive_link = upload_resume_to_drive(file_path, f"resume_{resume.id}.docx")
            resume.content_json["drive_link"] = drive_link
            db.commit()
        except Exception as e:
            print(f"Drive upload failed (non-fatal): {e}")

        return resume.id

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()