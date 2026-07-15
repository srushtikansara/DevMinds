import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Date, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    report_storage_uri = Column(String, nullable=True)
    summary_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))