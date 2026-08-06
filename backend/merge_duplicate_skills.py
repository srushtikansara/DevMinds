from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import Skill, SkillEvent, SkillSignal

USER_ID = "6878c9d9-5b64-4dc5-b78d-181fe7d56ff2"

MERGES = [
    ("deep_learning", "deep-learning"),
    ("generative_ai", "generative-ai"),
    ("machine_learning", "machine-learning"),
    ("neural_networks", "neural-networks"),
    ("gemini api", "gemini-api"),
    ("docker compose", "docker-compose"),
    ("rest api", "rest-api"),
    ("mcp (model context protocol)", "mcp"),
    ("cursor-editor", "cursor"),
    ("cursor-ide", "cursor"),
]

db = SessionLocal()
for duplicate_name, canonical_name in MERGES:
    dup = db.query(Skill).filter(Skill.user_id == USER_ID, Skill.skill_name == duplicate_name).first()
    canonical = db.query(Skill).filter(Skill.user_id == USER_ID, Skill.skill_name == canonical_name).first()

    if not dup or not canonical:
        print(f"Skipping {duplicate_name} -> {canonical_name} (one not found)")
        continue

    db.query(SkillEvent).filter(SkillEvent.skill_id == dup.id).update({"skill_id": canonical.id})
    db.query(SkillSignal).filter(SkillSignal.skill_name == duplicate_name).update({"skill_name": canonical_name})
    canonical.signal_count += dup.signal_count
    db.delete(dup)
    print(f"Merged {duplicate_name} -> {canonical_name}")

db.commit()
db.close()