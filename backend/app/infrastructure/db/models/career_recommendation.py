import uuid
from datetime import datetime,timezone

from sqlalchemy import Column,Boolean,Float,DateTime,ForeignKey,String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class CareerRecommendation(Base):
    __tablename__="career_recommendations"
    
    id= Column(UUID(as_uuid=False),primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False),ForeignKey("users.id"),nullable=False)
    job_postings_id = Column(UUID(as_uuid=False),ForeignKey("job_postings.id"),nullable=False)
    fit_score = Column(Float,nullable=False)
    fit_reason = Column(String,nullable=True)
    reviewed = Column(Boolean,nullable=False)
    created_at = Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    applied = Column(Boolean,default=False)
    rejected = Column(Boolean,default=False)