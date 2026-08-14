from typing import TypedDict, Optional
from anthropic import BaseModel
from langgraph import graph
from langgraph.graph import StateGraph, START, END
from tenacity import retry, stop_after_attempt, wait_fixed
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Skill,DeveloperEvent, SkillEvent, Memory
from app.infrastructure.embeddings.gemini_embeddings import get_embedding
from app.infrastructure.vectorstore.chroma_client import find_similar
from app.infrastructure.llm.gemini_provider import client
from app.infrastructure.jobs.himalayas_client import search_jobs
from tavily import TavilyClient
from pydantic import BaseModel, Field
from app.config import settings

tavily= TavilyClient(api_key=settings.tavily_api_key)
import json
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    
class NextStep(BaseModel):
    topic: str
    why: str
    how:str= Field(description="How to approach learning this. MUST explicitly name and include the actual URL of one relevant resource from the provided learning resources list, inline in this text.")
    
class RelearnSummary(BaseModel):
    tracked_history: str
    general_knowledge: str
    next_steps: list[NextStep]

class LearningAssistantState(TypedDict):
    user_id: str
    skill_name: str
    mode: Optional[str]
    signal_count: Optional[int]
    linked_events: Optional[list]
    related_memories: Optional[list]
    learning_plan: Optional[str]
    job_market_count: Optional[int]
    decision_log: list[str]
    web_resources: Optional[dict]

def fetch_skill_node(state: LearningAssistantState) -> LearningAssistantState:
    db = SessionLocal()
    skill = db.query(Skill).filter(
        Skill.user_id == state['user_id'],
        Skill.skill_name.ilike(state['skill_name'])
    ).first()

    linked_event_descriptions = []
    if skill:
        linked_events = (
            db.query(DeveloperEvent)
            .join(SkillEvent, SkillEvent.developer_event_id == DeveloperEvent.id)
            .filter(SkillEvent.skill_id == skill.id)
            .order_by(DeveloperEvent.occurred_at.desc())
            .limit(5)
            .all()
        )
        linked_event_descriptions = [e.description for e in linked_events]

    db.close()
    state['signal_count'] = skill.signal_count if skill else 0
    state['linked_events'] = linked_event_descriptions
    state['decision_log'].append(
        f"Skill '{state['skill_name']}' signal_count={state['signal_count']}, "
        f"{len(linked_event_descriptions)} directly linked real events"
    )
    return state

def search_related_memory_node(state: LearningAssistantState) -> LearningAssistantState:
    query_vector = get_embedding(state['skill_name'], task_type="RETRIEVAL_QUERY")
    matches = find_similar(query_vector, top_k=3)
    
    relevant_matches = [m for m in matches if (1 - m.get("distance", 1)) >= 0.5]
    state['related_memories'] = relevant_matches
    state['decision_log'].append(f"Found {len(matches)} related memories")
    return state


def route_learning_mode(state: LearningAssistantState) -> str:
    """The single, real router - checks mode FIRST, then falls back to signal-based routing."""
    if state.get("mode") == "relearn":
        return "relearn"
    return "getting_started" if state["signal_count"] == 0 else "next_level"


@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
def generate_relearn_summary_node(state: LearningAssistantState) -> LearningAssistantState:
    memories = state["related_memories"] or []
    linked_context = "\n".join(state.get("linked_events") or [])
    semantic_context = "\n".join(
        f"[via {m.get('source', 'unknown tool')}]: {m['text']}"
        for m in (state["related_memories"] or [])
    )
    web = state.get("web_resources") or {"youtube": [], "articles": [], "documentation": []}
    web_context = f"""
YouTube: {chr(10).join(f"- {r['title']}: {r['url']}" for r in web.get('youtube', []))}
Articles: {chr(10).join(f"- {r['title']}: {r['url']}" for r in web.get('articles', []))}
Documentation: {chr(10).join(f"- {r['title']}: {r['url']}" for r in web.get('documentation', []))}
"""

    prompt = f"""A developer wants a full relearn summary for: {state['skill_name']}

Directly linked real events for this skill (guaranteed relevant, highest confidence):
{linked_context if linked_context else "(no directly linked events yet)"}

Additional related memories (semantic search, broader context):
{semantic_context}

Real, current learning resources found for this skill:
{web_context}

Write your response in THREE clearly separated parts:

Provide:
1. A DETAILED summary of exactly what DevMind has real evidence you covered
   (tracked_history) - specific files, specific bugs, specific decisions. If there's
   little or no direct evidence, say so honestly.
2. Core concepts a developer at this level would typically know (general_knowledge) -
   clearly this is general knowledge, NOT verified from tracked work.
3. 2-3 specific next_steps to deepen this skill. For each: explain why it's the right
   next step given what's already been done, explain how to approach learning it
   (matching their real style if evident), and within the "how" field, explicitly
   name and reference at least one resource from the learning resources above if one
   is genuinely relevant to that specific topic.

"""
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config= {
            "response_mime_type": "application/json",
            "response_schema": RelearnSummary,
        })
    result: RelearnSummary = response.parsed
    
    next_steps_text = "\n\n".join(
        f"**{i+1}. {step.topic}**\nWhy: {step.why}\nHow: {step.how}"
        for i, step in enumerate(result.next_steps)
    )
    
    summary_text = f"""### PART 1 - What you've actually done (tracked history)
{result.tracked_history}

### PART 2 - General knowledge on {state['skill_name']} (not from your tracked history)
{result.general_knowledge}

### PART 3 - What to learn next, and how
{next_steps_text}
"""

    if state.get("linked_events"):
        events_list = "\n".join(f"- {e}" for e in state["linked_events"])
        summary_text += f"\n\n---\n**Real linked events used for this summary:**\n{events_list}"
    else:
        summary_text += "\n\n---\n**No directly linked events found for this skill yet.**"

    state["learning_plan"] = summary_text
    return state

@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
def generate_plan_node(state: LearningAssistantState, mode: str) -> LearningAssistantState:
    linked_context = "\n".join(state.get("linked_events") or [])
    semantic_context = "\n".join(
        f"[via {m.get('source', 'unknown tool')}]: {m['text']}"
        for m in (state["related_memories"] or [])
    )

    prompt = f"""You are this developer's ongoing technical mentor - you've been watching
their real work over time, not meeting them for the first time.

Skill in focus: {state['skill_name']}
Their experience level with it: {"complete beginner - no prior signal" if mode == "getting_started" else "some existing exposure, ready to go deeper"}

Directly linked real events for this skill (guaranteed relevant, highest confidence):
{linked_context if linked_context else "(none directly linked yet)"}

Additional related memories (semantic search, broader context):
{semantic_context}

IMPORTANT: Base your response ONLY on the specific facts above. Do not invent details
not explicitly present in this text.

As their mentor, write:
1. One sentence acknowledging specifically what you've seen them do already, quoting or
   closely paraphrasing an actual detail from the sources above
2. A concise, 3-step plan for what to focus on next, building directly on that real work
3. One honest sentence about the single biggest gap holding them back right now
4. A brief note on HOW to learn this effectively, given their specific style - e.g.
   "given you learn by building real integrations rather than reading docs first,
   I'd skip the theory and go straight to step 1" - genuinely tailored to the pattern
   you observe in their real work, not generic study advice
5. One sentence explaining WHY you chose this particular plan over alternatives -
   what specifically in their real history led you here, so they can see your reasoning,
   not just the conclusion
   
   Real, current learning resources found for this skill:
YouTube: {chr(10).join(f"- {r['title']}: {r['url']}" for r in state.get('web_resources', {}).get('youtube', []))}
Articles: {chr(10).join(f"- {r['title']}: {r['url']}" for r in state.get('web_resources', {}).get('articles', []))}
Documentation: {chr(10).join(f"- {r['title']}: {r['url']}" for r in state.get('web_resources', {}).get('documentation', []))}

If relevant, reference specific resources above by name in your plan.

"""
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    summary_text = response.text

    if state.get("linked_events"):
        events_list = "\n".join(f"- {e}" for e in state["linked_events"])
        summary_text += f"\n\n---\n**Real linked events used for this summary:**\n{events_list}"
    else:
        summary_text += "\n\n---\n**No directly linked events found for this skill yet.**"

    state["learning_plan"] = summary_text
    state["decision_log"].append("Generated cross-tool relearn summary (tracked + general knowledge)")
    return state

def search_learning_resources_node(state: LearningAssistantState) -> LearningAssistantState:
    skill = state['skill_name']
    cache_key = f"web_resources:{skill}"

    cached = redis_client.get(cache_key)
    if cached:
        state["web_resources"] = json.loads(cached)
        state["decision_log"].append(f"Found cached web resources for {skill}")
        return state
    resources = {"youtube": [], "articles": [], "documentation": []}
    try:
        yt_results = tavily.search(
            query=f"best Youtube tutorial or guide to learn {state['skill_name']} for developers",
            max_results=2,
            include_domains=["youtube.com"],
        )
        resources["youtube"] = [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in yt_results.get("results", [])
        ]
    except Exception as e:
        
        print(f"Tavily search failed (non-fatal): {e}")
        
    try:
        article_results = tavily.search(
            query=f"best article or blog post explaining {skill} in depth for developers",
            max_results=2,
            exclude_domains=["youtube.com"],
        )
        resources["articles"] = [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in article_results.get("results", [])
        ]
    except Exception as e:
        print(f"Article search failed (non-fatal): {e}")
        
    try:
        doc_results = tavily.search(
            query=f"{skill} official documentation getting started guide",
            max_results=2,
        )
        resources["documentation"] = [
            {"title": r.get("title", ""), "url": r.get("url", "")}
            for r in doc_results.get("results", [])
        ]
    except Exception as e:
        print(f"Documentation search failed (non-fatal): {e}") 
        
    redis_client.setex(cache_key, 86400, json.dumps(resources))
    state["web_resources"] = resources
    total = sum(len(v) for v in resources.values())
    state["decision_log"].append(f"Found {total} real web resources for {state['skill_name']}")
    return state

def check_learning_path_progress(skill_path: list[str], user_id: str) -> dict:
    db = SessionLocal()
    try:
        results = []
        for skill_name in skill_path:
            skill = (
                db.query(Skill)
                .filter(Skill.user_id == user_id, Skill.skill_name.ilike(skill_name))
                .first()
            )

            linked_count = 0
            signal_count = 0
            if skill:
                linked_count = db.query(SkillEvent).filter(SkillEvent.skill_id == skill.id).count()
                signal_count = skill.signal_count

            if linked_count >= 3:
                status = "learned"
            elif linked_count >= 1:
                status = "some_exposure"
            elif signal_count > 0:
                status = "minimal_signal"
            else:
                status = "not_started"

            results.append({
                "skill_name": skill_name,
                "status": status,
                "linked_events": linked_count,
                "signal_count": signal_count,
            })

        gaps = [r["skill_name"] for r in results if r["status"] in ("not_started", "minimal_signal")]
        return {"path": results, "next_gap": gaps[0] if gaps else None}
    finally:
        db.close()
        
def suggest_learning_path(goal: str, user_id: str) -> dict:
    prompt = f"""A developer wants to achieve this goal: "{goal}"

Propose an ordered list of 3-6 specific, foundational-to-advanced skills or
technologies they should learn, in the order that makes sense for genuinely
building toward this goal. Use real, specific, well-known skill/technology
names (e.g. "langchain", "langgraph", "postgresql"), not vague phrases.

Respond as a JSON array of lowercase skill names only, in order, like:
["python", "langchain", "langgraph", "mcp"]
"""
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    text = str(response.text).strip()

    import re, json as jsonlib
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return {"error": "Could not parse a valid skill path from the model's response"}

    try:
        suggested_order = jsonlib.loads(match.group(0))
    except jsonlib.JSONDecodeError:
        return {"error": "Could not parse a valid skill path from the model's response"}

    progress = check_learning_path_progress(suggested_order, user_id)

    next_recommended = None
    for entry in progress["path"]:
        if entry["status"] in ("not_started", "minimal_signal"):
            next_recommended = entry["skill_name"]
            break

    return {
        "goal": goal,
        "suggested_order": suggested_order,
        "order_note": "This order is general, common-practice guidance - not personalized to your history.",
        "your_real_progress": progress["path"],
        "recommended_next": next_recommended,
    }

def getting_started_node(state):
    return generate_plan_node(state, "getting_started")


def next_level_node(state):
    return generate_plan_node(state, "next_level")


def check_job_market_node(state: LearningAssistantState) -> LearningAssistantState:
    jobs = search_jobs(state['skill_name'], limit=10)
    state['job_market_count'] = len(jobs)
    state["decision_log"].append(f"Found {len(jobs)} current job postings mentioning this skill")
    return state

def route_after_market(state: LearningAssistantState) -> str:

    return "search_resources"


def build_learning_agent():
    graph = StateGraph(LearningAssistantState)

    graph.add_node("fetch_skill", fetch_skill_node)
    graph.add_node("search_memory", search_related_memory_node)
    graph.add_node("relearn_summary", generate_relearn_summary_node)
    graph.add_node("getting_started", getting_started_node)
    graph.add_node("next_level", next_level_node)
    graph.add_node("check_market", check_job_market_node)
    graph.add_node("search_resources", search_learning_resources_node)
    # REMOVED: graph.add_node("route_after_market", route_after_market)

    graph.add_edge(START, "fetch_skill")
    graph.add_edge("fetch_skill", "search_memory")

    graph.add_conditional_edges("search_memory", route_learning_mode, {
        "relearn": "relearn_summary",
        "getting_started": "getting_started",
        "next_level": "next_level",
    })

    graph.add_edge("relearn_summary", "check_market")
    graph.add_edge("getting_started", "check_market")
    graph.add_edge("next_level", "check_market")

    # REMOVED: graph.add_edge("check_market", "route_after_market")
    graph.add_conditional_edges(
        "check_market",
        route_after_market,
        {"search_resources": "search_resources", "END": END},
    )
    graph.add_edge("search_resources", END)
    # REMOVED: duplicate graph.add_edge("search_resources", END)

    return graph.compile()