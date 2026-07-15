import uuid

from sqlalchemy import Column,String,ForeignKey

from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.db.base import Base 

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=False), primary_key=True , default=lambda:str(uuid.uuid4()))
    memory_id = Column(UUID(as_uuid=False),ForeignKey("memories.id"),unique = True , nullable= False)
    chroma_id = Column(String,nullable=False)
    model_version= Column(String,nullable=False)