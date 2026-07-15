import uuid 
from sqlalchemy import Column,String,DateTime,ForeignKey

from datetime import timezone,datetime
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class Session(Base):
    
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=False), primary_key=True , default=lambda:str (uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False),ForeignKey("users.id"),nullable=False)
    connector_id = Column(UUID(as_uuid=False),ForeignKey("connectors.id"),nullable=False)
    session_upload_id = Column(String,nullable=False, unique=True)
    raw_storage_uri = Column(String, nullable=True)
    status = Column(String,default="queued")
    started_at = Column(DateTime(timezone=True),nullable=True)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
