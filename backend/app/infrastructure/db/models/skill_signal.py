import uuid

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class SkillSignal(Base):
    __tablename__ = "skill_signals"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    developer_event_id = Column(UUID(as_uuid=False), ForeignKey("developer_events.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    weight = Column(Float, default=1.0)