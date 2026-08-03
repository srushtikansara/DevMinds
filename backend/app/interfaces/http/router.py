from datetime import datetime
import json
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile,File
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.infrastructure.db.session import get_db
from app.infrastructure.db.models import Session as SessionModel, Connector, User , Memory,Recommendation,CareerRecommendation,JobPosting,Resume
from app.infrastructure.embeddings.gemini_embeddings import get_embedding 
from app.infrastructure.vectorstore.chroma_client import find_similar
from app.infrastructure.db.models import DeveloperProfile,WeeklyReport
from app.infrastructure.llm.gemini_provider import tailor_resume_for_job
from app.interfaces.http.auth import get_current_user
from app.infrastructure.notion.notion_client import log_application
from workers.resume_worker import generate_resume
from fastapi.responses import FileResponse
from workers.agent_worker import run_learning_agent
from app.infrastructure.queue.celery_app import celery_app
from datetime import date
from workers.parser_worker import parse_session

router = APIRouter()
RAW_SESSIONS_DIR = "raw_sessions"
os.makedirs(RAW_SESSIONS_DIR, exist_ok=True)
UPLOADED_RESUMES_DIR = "uploaded_resumes"
os.makedirs(UPLOADED_RESUMES_DIR, exist_ok=True)

VALID_TOOL_TYPES = {"claude_code", "cursor", "codex", "antigravity", "github"}


class SessionUploadRequest(BaseModel):
    session_upload_id: str
    tool_type: str
    started_at: datetime
    payload: dict

class RoleInput(BaseModel):
    title: str
    context: str
    start_date: str
    end_date: str = "Present"
    type: str = "project"  # "project" or "experience"


class EducationInput(BaseModel):
    degree: str
    institution: str
    graduation_date: str


class ResumeGenerationRequest(BaseModel):
    full_name: str
    email: str
    phone: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    education: list[EducationInput]
    roles: list[RoleInput]
    
@router.post("/sessions", status_code=202)
def upload_session(body: SessionUploadRequest, user: User = Depends(get_current_user) ,db: DBSession = Depends(get_db)):

    if body.tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(400, f"tool_type must be one of {sorted(VALID_TOOL_TYPES)}")

    existing = (
        db.query(SessionModel)
        .filter(SessionModel.session_upload_id == body.session_upload_id)
        .first()
    )
    if existing:
        return {"session_id": existing.id, "status": existing.status}

    connector = (
        db.query(Connector)
        .filter(Connector.user_id == user.id, Connector.tool_type == body.tool_type)
        .first()
    )
    if connector is None:
        connector = Connector(user_id=user.id, tool_type=body.tool_type, status="active")
        db.add(connector)
        db.flush()

    try:
        raw_path = os.path.join(RAW_SESSIONS_DIR,f"{body.session_upload_id}.json")
        with open(raw_path,"w") as f:
            json.dump(body.payload,f)
            
        session = SessionModel(
            user_id=user.id,
            connector_id=connector.id,
            session_upload_id=body.session_upload_id,
            status="queued",
            started_at=body.started_at,
            raw_storage_uri=raw_path,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        parse_session.delay(session.id)
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(SessionModel)
            .filter(SessionModel.session_upload_id == body.session_upload_id)
            .first()
        )
        return {"session_id": existing.id, "status": existing.status}

    return {"session_id": session.id, "status": "queued"}

@router.get("/memories/search")
def search_name(q: str, user: User = Depends(get_current_user) ,db: DBSession = Depends(get_db)):
    if not q or not q.strip():
        raise HTTPException(400, "Query cannot be empty")
    if len(q) > 500:
        raise HTTPException(422, "Query too long (500 max characters)")

    query_vector = get_embedding(q, task_type="RETRIEVAL_QUERY")

    matches = find_similar(query_vector, top_k=10)

    results = []

    for match in matches:
        try:
            memory = db.query(Memory).filter(Memory.id == match["memory_id"]).first()
        except Exception:
            db.rollback()
            continue  

        if memory is None:
            continue

        similarity = 1 - match["distance"]
        results.append({
            "memory_id": memory.id,
            "content": memory.content,
            "importance_score": memory.importance_score,
            "similarity": round(similarity, 3),
        })

    results.sort(key=lambda r: (r["similarity"] * 0.7 + r["importance_score"] * 0.3), reverse=True)
    return {"query": q, "results": results}

@router.get("/profile")
def get_profile(user: User = Depends(get_current_user),db: DBSession = Depends(get_db)):
    profile = db.query(DeveloperProfile).filter(DeveloperProfile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(404, "Profile not yet computed - upload at least one session first")

    return {
        "user_id": profile.user_id,
        "skill_summary": profile.skill_summary,
        "activity_summary": profile.activity_summary,
        "last_computed_at": profile.last_computed_at,
    }
    
@router.get("/reports/{week_start}")
def get_weekly_report( week_start: date,user: User = Depends(get_current_user) , db: DBSession = Depends(get_db)):
   
    report= (
        db.query(WeeklyReport)
        .filter(WeeklyReport.user_id == user.id, WeeklyReport.week_start == week_start)
        .first()
    )
    
    if report is None:
        raise HTTPException(404, f"No report generated for week starting {week_start}")

    return {
        "week_start": report.week_start,
        "report_storage_uri": report.report_storage_uri,
        "summary_json": report.summary_json,
        "generated_at": report.generated_at,
    }

@router.get("/resumes/{resume_id}/download")
def download_resume(resume_id:str,user: User =Depends(get_current_user)):
    file_path = f"generated_resumes/resume_{resume_id}.docx"
    if not os.path.exists(file_path):
        raise HTTPException(404, "Resume file not found")
    return FileResponse(file_path, filename="resume.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.post("/resumes/generate",status_code=202)
def request_resume_generation(
    body: ResumeGenerationRequest,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    task = generate_resume.delay(user.id, body.model_dump())
    return {"status": "queued", "task_id": task.id}


@router.get("/recommendations")
def get_recommendations(user:User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id, Recommendation.actioned == False)
        .order_by(Recommendation.relevance_score.desc())
        .all()
    )
    return {
        "recommendations": [
            {"content": r.content, "relevance_score": r.relevance_score, "type": r.type}
            for r in recommendations
        ]
    }
@router.post("/learning/coach/{skill_name}")
def get_learning_coaching(skill_name: str,  relearn: bool = False, user: User = Depends(get_current_user)):
    task = run_learning_agent.delay(user.id, skill_name,"relearn" if relearn else None)
    return {"status": "queued", "task_id": task.id}


@router.get("/learning/coach/result/{task_id}")
def get_learning_coaching_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if not result.ready():
        return {"status": "pending"}
    return {"status": "complete", "result": result.result}

@router.post("/resumes/upload",status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if not file.filename.lower().endswith((".pdf",".docx")):
        raise HTTPException(422,"Only .pdf and .docx files are supported")
    
    from app.infrastructure.documents.resume_parser import extract_resume_text
    
    saved_path = os.path.join(UPLOADED_RESUMES_DIR,file.filename)
    with open(saved_path,"wb") as f:
        shutil.copyfileobj(file.file,f)
    
    try:
        extracted_text = extract_resume_text(saved_path,file.filename)
    except Exception as e:
        raise HTTPException(422, f"Could not parse file: {str(e)}")

    if not extracted_text.strip():
        raise HTTPException(422,"No readable text found in the uploaded file")
    
    resume = Resume(
        user_id = user.id,
        content_json = {"raw_text": extracted_text},
        source="uploaded",
        version=1
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    return {"resume_id": resume.id, "status": "uploaded", "text_length": len(extracted_text)}
    
@router.get("/resumes")
def list_resumes(user:User = Depends(get_current_user),db:DBSession =Depends(get_db)):
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id==user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )   
    
    return {
        "resumes": [
            {
                "id": r.id,
                "source":r.source,
                "version": r.version,
                "created_at": r.created_at,
            }
            for r in resumes
        ]
    }   

@router.get("/resumes/{resume_id}")
def get_resume_detail(resume_id:str, user:User = Depends(get_current_user),db: DBSession = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id,  Resume.user_id == user.id).first()
    if resume is None:
        raise HTTPException(404,"Resume not found")
    
    return {"id": resume.id,
        "source": resume.source,
        "version": resume.version,
        "content_json": resume.content_json,
        "created_at": resume.created_at,
    }
    
@router.post("/career/matches/{recommendation_id}/reject")
def reject_match(recommendation_id:str , user: User =Depends(get_current_user),db:DBSession = Depends(get_db)):
    recommendation = (
        db.query(CareerRecommendation)
        .filter(CareerRecommendation.id == recommendation_id,CareerRecommendation.user_id == user.id)
        .first()
    )
    if recommendation is None:
        raise HTTPException(404,"Recommendation not found")
    
    recommendation.reviewed=True
    recommendation.rejected=True
    db.commit()
    
    return {"status": "rejected"}
@router.get("/career/matches")
def get_career_matches(user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    matches = (
        db.query(CareerRecommendation, JobPosting)
        .join(JobPosting, CareerRecommendation.job_postings_id == JobPosting.id)
        .filter(CareerRecommendation.user_id == user.id, CareerRecommendation.rejected == False)
        .order_by(CareerRecommendation.fit_score.desc())
        .all()
    )
    return {
        "matches": [
            {
                "id": rec.id,
                "title": posting.title,
                "company": posting.company,
                "location": posting.location,
                "url": posting.url,
                "fit_score": rec.fit_score,
                "fit_reason": rec.fit_reason,
                "applied": rec.applied,
                "reviewed" : rec.reviewed
            }
            for rec, posting in matches
        ]
    }
@router.post("/career/matches/{recommendation_id}/prepare")
def prepare_application(recommendation_id: str, user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    recommendation = (
        db.query(CareerRecommendation)
        .filter(CareerRecommendation.id == recommendation_id, CareerRecommendation.user_id == user.id)
        .first()
    )
    if recommendation is None:
        raise HTTPException(404, "Recommendation not found")

    posting = db.query(JobPosting).filter(JobPosting.id == recommendation.job_postings_id).first()

    base_resume = (
        db.query(Resume)
        .filter(Resume.user_id == user.id, Resume.source.in_(["generated", "uploaded"]))
        .order_by(Resume.created_at.desc())
        .first()
    )

    if base_resume is None:
        raise HTTPException(400, "No base resume - generate a resume first before preparing an application")

    tailored_content = tailor_resume_for_job(
        base_resume_content=base_resume.content_json,
        job_title=posting.title,
        job_description=posting.description
    )

    tailored_resume = Resume(
        user_id=user.id,
        content_json=tailored_content,
        source="tailored",
        version=1
    )
    try:
        log_application(posting.title, posting.company, recommendation.fit_score, tailored_content["summary"])
    except Exception as e:
        print(f"Notion logging failed (non-fatal): {e}")

    db.add(tailored_resume)
    recommendation.reviewed = True
    db.commit()
    db.refresh(tailored_resume)

    return {
        "status": "reviewed",
        "job_title": posting.title,
        "company": posting.company,
        "apply_url": posting.url,
        "tailored_resume_id": tailored_resume.id,
        "tailored_summary": tailored_content["summary"],
        "highlighted_skills": tailored_content["highlighted_skills"],
        "tailoring_notes": tailored_content["tailoring_notes"],
    }
@router.post("/career/matches/{recommendation_id}/mark-applied")
def mark_applied(recommendation_id:str , user: User = Depends(get_current_user),db: DBSession = Depends(get_db)):
    recommendation = (
        db.query(CareerRecommendation)
        .filter(CareerRecommendation.id == recommendation_id, CareerRecommendation.user_id == user.id)
        .first()
    )
    if recommendation is None:
        raise HTTPException(404,"Recommendation not found")
    
    if not recommendation.reviewed:
        raise HTTPException(
            400,
            "This reommendation hasn't been prepared yet. Call /prepare first before marking is applied."
        )
    if recommendation.rejected:
        raise HTTPException(
            400,
            "This recommendation was rejected - cannot mark a rejected job as applied."
          )
    recommendation.applied = True
    db.commit()
    
    return {"status": "marked as applied"}

@router.get("/career/applied")
def get_applied_jobs(user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    matches = (
        db.query(CareerRecommendation, JobPosting)
        .join(JobPosting, CareerRecommendation.job_postings_id == JobPosting.id)
        .filter(CareerRecommendation.user_id == user.id, CareerRecommendation.applied == True)
        .order_by(CareerRecommendation.created_at.desc())
        .all()
    )
    return {
        "applied": [
            {
                "title": posting.title,
                "company": posting.company,
                "location": posting.location,
                "url": posting.url,
                "fit_score": rec.fit_score,
            }
            for rec, posting in matches
        ]
    }