import uuid

from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, Text, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class Memory(Base):

    __tablename__ = "memories"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    source_event_id = Column(UUID(as_uuid=False), ForeignKey("developer_events.id"), nullable=False)
    content = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.5)
    version = Column(Integer, default=1)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))