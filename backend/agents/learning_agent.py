from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from tenacity import retry, stop_after_attempt, wait_fixed

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Skill,DeveloperEvent, SkillEvent, Memory
from app.infrastructure.embeddings.gemini_embeddings import get_embedding
from app.infrastructure.vectorstore.chroma_client import find_similar
from app.infrastructure.llm.gemini_provider import client
from app.infrastructure.jobs.himalayas_client import search_jobs
from tavily import TavilyClient
from app.config import settings

tavily= TavilyClient(api_key=settings.tavily_api_key)
import json


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
    web_resources: Optional[list]

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

    prompt = f"""A developer wants to relearn: {state['skill_name']}

Directly linked real events for this skill (guaranteed relevant, highest confidence):
{linked_context if linked_context else "(no directly linked events yet - this skill may lack tracked signal)"}

Additional related memories (semantic search, broader context):
{semantic_context}

STEP 1 - Honest assessment (do this first, silently, before writing anything):
Do the sources above ACTUALLY discuss '{state['skill_name']}' itself, or are they about
different, only tangentially related infrastructure or tools?

STEP 2 - Write your response based on that assessment:

IF genuinely about {state['skill_name']}:
- Summarize specifically what was covered, prioritizing the directly linked events above
  as your primary source, using memories only as supplementary context
- Note which tool each piece of work came from, if indicated
- Suggest 2-3 genuinely NEW angles or deeper concepts not already covered

IF NOT actually about {state['skill_name']} (just adjacent/related work):
- Say so plainly, in your first sentence
- Then describe the related work that DOES exist, and how it could serve as a bridge
- Do NOT present adjacent work as if it were direct experience

Do not invent details not explicitly present in the sources above.
"""
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    state["learning_plan"] = response.text
    state["decision_log"].append("Generated cross-tool relearn summary")
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
    state["learning_plan"] = response.text
    state["decision_log"].append(f"Generated {mode} plan")
    return state

def search_learning_resources_node(state: LearningAssistantState) -> LearningAssistantState:
    skill = state['skill_name']
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
        resources = []
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

    state["web_resources"] = resources
    state["decision_log"].append(f"Found {len(resources)} real web resources for {state['skill_name']}")
    return state


def getting_started_node(state):
    return generate_plan_node(state, "getting_started")


def next_level_node(state):
    return generate_plan_node(state, "next_level")


def check_job_market_node(state: LearningAssistantState) -> LearningAssistantState:
    jobs = search_jobs(state['skill_name'], limit=10)
    state['job_market_count'] = len(jobs)
    state["decision_log"].append(f"Found {len(jobs)} current job postings mentioning this skill")
    return state


def build_learning_agent():
    graph = StateGraph(LearningAssistantState)

    graph.add_node("fetch_skill", fetch_skill_node)
    graph.add_node("search_memory", search_related_memory_node)
    graph.add_node("relearn_summary", generate_relearn_summary_node)
    graph.add_node("getting_started", getting_started_node)
    graph.add_node("next_level", next_level_node)
    graph.add_node("check_market", check_job_market_node)
    graph.add_node("search_resources", search_learning_resources_node)

    graph.add_edge(START, "fetch_skill")
    graph.add_edge("fetch_skill", "search_memory")

    # The ONE real router, checking relearn mode first
    graph.add_conditional_edges("search_memory", route_learning_mode, {
        "relearn": "relearn_summary",
        "getting_started": "getting_started",
        "next_level": "next_level",
    })

    graph.add_edge("relearn_summary", "check_market")
    graph.add_edge("getting_started", "check_market")
    graph.add_edge("next_level", "check_market")
    graph.add_edge("check_market", "search_resources")
    graph.add_edge("search_resources", END)

    return graph.compile()