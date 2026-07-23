import uuid
from datetime import datetime,timezone
from sqlalchemy import Column,String,Text,DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class JobPosting(Base):
    
    __tablename__="job_postings"
    
    id = Column(UUID(as_uuid=False),primary_key=True,default=lambda:str(uuid.uuid4()))
    external_id = Column(String,unique=True,nullable=False)
    title = Column(String,nullable=False)
    company = Column(String,nullable=False)
    location = Column(String,nullable=False)
    description = Column(Text,nullable=False)
    url = Column(String,nullable=False)
    source = Column(String,default="aduzna")
    fetched_at = Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    
    