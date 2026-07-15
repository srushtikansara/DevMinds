import uuid 

from datetime import datetime,timezone
from sqlalchemy import Column,String , ForeignKey ,JSON, DateTime,Integer
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class DeveloperProfile(Base):
    __tablename__ = "developer_profiles"
    
    id = Column(UUID(as_uuid=False),primary_key=True, default=lambda:str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False ,unique=True)
    skill_summary = Column(JSON, nullable=False)
    activity_summary = Column(JSON, nullable=True)
    version = Column(Integer, default=1)
    last_computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    