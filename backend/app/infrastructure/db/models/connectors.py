import uuid

from sqlalchemy import Column, String , DateTime ,ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base 

class Connector(Base):
    __tablename__= "connectors"
    
    id = Column(UUID(as_uuid=False),primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False),ForeignKey("users.id"), nullable=False )
    tool_type = Column(String,nullable=False)
    status = Column(String, default="active")
    last_sync_on=Column(DateTime(timezone=True),nullable=True)
    