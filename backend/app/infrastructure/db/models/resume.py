import uuid
from datetime import datetime,timezone
from sqlalchemy import Column,String,ForeignKey,Integer,JSON,DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class Resume(Base):
    __tablename__= "resumes"
    
    id = Column(UUID(as_uuid= False), primary_key=True , default=lambda:str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid= False),ForeignKey("users.id"),nullable=False)
    content_json=Column(JSON,nullable=False)
    source = Column(String,default="generated")
    version = Column(Integer,default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    
    