from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperEvent, SkillEvent, Skill
from workers.skill_worker import process_skills

db = SessionLocal()
already_linked_event_ids = {row.developer_event_id for row in db.query(SkillEvent.developer_event_id).distinct()}
all_events = db.query(DeveloperEvent.id).filter(DeveloperEvent.technology_tags.isnot(None)).all()
db.close()

to_process = [str(e.id) for e in all_events if str(e.id) not in already_linked_event_ids]
print(f"Backfilling {len(to_process)} unlinked events...")

for event_id in to_process:
    result = process_skills.delay(event_id)
    print(event_id, "->", result.id)