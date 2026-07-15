import uuid

from sqlalchemy import Column , Integer , DateTime ,ForeignKey ,JSON
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base

class Conversation(Base):
    __tablename__="conversations"
    
    id= Column(UUID(as_uuid=False),primary_key=True, default=lambda:str(uuid.uuid4()))
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id") ,  nullable=False)
    turn_count = Column(Integer , default=0)
    structured_content = Column(JSON , nullable=True)