import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    proficiency_score = Column(Float, default=0.0)
    signal_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))