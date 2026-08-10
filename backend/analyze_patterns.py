import sys
sys.path.insert(0, r"C:\Users\Srushti\Desktop\DevMind\backend")

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperEvent, SkillEvent, Skill
from app.infrastructure.llm.gemini_provider import client


def analyze_learning_patterns(user_id: str) -> dict:
    db = SessionLocal()
    events = (
        db.query(DeveloperEvent.description, Skill.skill_name)
        .join(SkillEvent, SkillEvent.developer_event_id == DeveloperEvent.id)
        .join(Skill, Skill.id == SkillEvent.skill_id)
        .filter(Skill.user_id == user_id)
        .order_by(DeveloperEvent.occurred_at.desc())
        .limit(50)
        .all()
    )
    db.close()

    if len(events) < 15:
        return {"pattern": None, "confidence": "insufficient_data", "based_on": len(events)}

    events_text = "\n".join(f"[{skill}] {desc}" for desc, skill in events)

    prompt = f"""Here are a developer's real, tracked activity events across MULTIPLE
different skills:

{events_text}

Look HONESTLY for a genuine, consistent pattern in HOW this developer approaches
learning/problem-solving - not what they learned, but their actual process.

If you see a real, consistent pattern across MULTIPLE different skills (not just one),
describe it in 1-2 sentences, citing which skills show it.

If the pattern actually varies by skill/domain, or there isn't enough consistency to
call it a real pattern, say so honestly instead of forcing one.

Respond in this exact format:
PATTERN: <description, or "No consistent pattern found - approach appears to vary by domain">
CONFIDENCE: <high|medium|low>
EVIDENCE: <which specific skills/events support this>
"""
    response = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    return {"raw_response": response.text, "based_on": len(events)}


if __name__ == "__main__":
    result = analyze_learning_patterns("6878c9d9-5b64-4dc5-b78d-181fe7d56ff2")
    print(f"Based on {result.get('based_on', 0)} real events\n")
    print(result.get("raw_response", "Insufficient data - need at least 15 tracked events"))