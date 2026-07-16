import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Float, Text, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class DeveloperEvent(Base):
    __tablename__ = "developer_events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)
    technology_tags = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    description = Column(Text, nullable=False)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))