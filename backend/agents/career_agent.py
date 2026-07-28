from typing import TypedDict,Optional
from langgraph.graph import StateGraph,END,START

from app.infrastructure.embeddings.gemini_embeddings import get_embedding
from app.infrastructure.vectorstore.chroma_client import find_similar
from app.infrastructure.db.models import Resume,JobPosting,CareerRecommendation
from app.infrastructure.llm.gemini_provider import tailor_resume_for_job
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.llm.gemini_provider import research_company
from agents.tools import research_company_web

class CareerAgentState(TypedDict):
    recommendation_id:str
    user_id:str
    job_title:Optional[str]
    fit_score: Optional[int]
    job_description: Optional[str]
    similar_past_work: Optional[str]
    tailored_summary: Optional[str]
    decision_log: list[str]
    company_search: Optional[str]
    
    
def fetch_job_node(state: CareerAgentState) -> CareerAgentState:
    db = SessionLocal()
    rec = db.query(CareerRecommendation).filter(CareerRecommendation.id == state["recommendation_id"]).first()
    posting = db.query(JobPosting).filter(JobPosting.id == rec.job_postings_id).first()
    db.close()
    
    state['job_title'] = posting.title
    state['fit_score'] = rec.fit_score
    state['job_description'] = posting.description
    state["decision_log"].append(f"Fetched job: {posting.title}, fit_score={rec.fit_score}")
    return state

def research_company_node(state: CareerAgentState) -> CareerAgentState:
    db = SessionLocal()
    rec = db.query(CareerRecommendation).filter(CareerRecommendation.id == state["recommendation_id"]).first()
    posting = db.query(JobPosting).filter(JobPosting.id == rec.job_postings_id).first()
    db.close()

    research = research_company_web(posting.company)
    state["company_research"] = research["summary"]
    state["decision_log"].append(f"Researched {posting.company} via grounded search")
    return state

def should_pursue(state:CareerAgentState) -> CareerAgentState:
    """The agentic decision point - routes based on real data, not a fixed script."""
    if state["fit_score"] >= 0.4:
        return "search_memory"
    return "skip"

def search_memory_node(state:CareerAgentState) -> CareerAgentState:
    query_vector = get_embedding(state["job_description"][:500], task_type="RETRIEVAL_QUERY")
    matches = find_similar(query_vector, top_k=5)
    state["similar_past_work"] = matches
    state["decision_log"].append(f"Found {len(matches)} similar past memories")
    return state

def tailor_node(state:CareerAgentState) -> CareerAgentState:
    db = SessionLocal()
    base_resume = (
        db.query(Resume)
        .filter(Resume.user_id == state["user_id"],Resume.source.in_(["generated", "uploaded"]))
        .order_by(Resume.created_at.desc())
        .first()
    )    
    db.close()
    
    tailored = tailor_resume_for_job(base_resume.content_json, state["job_title"], state["job_description"])
    state["tailored_summary"] = tailored["summary"]
    state["decision_log"].append("Tailored resume for this job")
    return state

def skip_node(state:CareerAgentState) -> CareerAgentState:
    state["decision_log"].append(f"Skipped - fit_score {state['fit_score']} below 0.4 threshold")
    return state

def build_career_agent():
    graph = StateGraph(CareerAgentState)
    graph.add_node("fetch_job", fetch_job_node)
    graph.add_node("research_company", research_company_node)
    graph.add_node("search_memory", search_memory_node)
    graph.add_node("tailor", tailor_node)
    graph.add_node("skip", skip_node)
    
    graph.add_edge(START, "fetch_job")
    graph.add_edge("fetch_job", "research_company")
    graph.add_conditional_edges("research_company", should_pursue,{"search_memory": "search_memory", "skip": "skip"})
    graph.add_edge("search_memory","tailor")
    graph.add_edge("tailor",END)
    graph.add_edge("skip",END)
    
    return graph.compile()