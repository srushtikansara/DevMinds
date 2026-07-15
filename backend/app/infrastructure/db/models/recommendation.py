import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # constrained set, e.g. "next_technology"
    content = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    actioned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))