import uuid
from datetime import datetime,timezone

from sqlalchemy import Column, String ,DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.db.base import Base

class User(Base):
    
    __tablename__ =  "users"
    
    id = Column(UUID(as_uuid = False), primary_key = True  , default = lambda:str(uuid.uuid4()))
    email = Column (String ,unique= True , nullable = False, )
    api_key_hash=Column (String ,nullable=False)
    created_at = Column(DateTime(timezone=True), default = lambda: datetime.now(timezone.utc))