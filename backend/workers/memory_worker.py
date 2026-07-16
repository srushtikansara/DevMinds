from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models import DeveloperEvent,Memory,Embedding
from app.infrastructure.embeddings.gemini_embeddings import get_embedding
from app.infrastructure.vectorstore.chroma_client import add_embedding,find_similar


SIMILARITY_THRESHOLD =0.92
@celery_app.task(name="process_memory",bind=True,max_retries = 3,default_retry_delay =10)
def process_memory(self,developer_event_id:str):
    db = SessionLocal()
    try:
        event = db.query(DeveloperEvent).filter(DeveloperEvent.id== developer_event_id).first()
        if event is None:
            raise ValueError(f"DeveloperEvent {developer_event_id} not found")
        
        vector = get_embedding(event.description,task_type="RETRIEVAL_DOCUMENT")
        candidates = find_similar(vector,top_k=2)
        
        if candidates:
            best_match = candidates[0]
            similarity = 1- best_match["distance"]
            
            if similarity >= SIMILARITY_THRESHOLD:
                
                memory = db.query(Memory).filter(Memory.id == best_match["memory_id"]).first()
                if memory:
                    memory.importance_score=min(1.0,memory.importance_score + 0.1)
                    memory.version +=1
                    db.commit()
                    return{"action": "reinforced","memory_id": memory.id ,"similarity": similarity}
                
        memory=Memory(
            user_id = event.user_id,
            source_event_id = event.id,
            content = event.description,
            importance_score =0.5,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        add_embedding(memory.id,vector,memory.content)
        embedding_row= Embedding(
            memory_id = memory.id,
            chroma_id = memory.id,
            model_version = "gemini-embedding-001",
        )
        db.add(embedding_row)
        db.commit()
        return{"action": "created","memory_id": memory.id}
    
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()