import hashlib

from fastapi import Depends,HTTPException,Header
from sqlalchemy.orm import Session as DBSession

from app.infrastructure.db.session import SessionLocal, get_db
from app.infrastructure.db.models import User


def get_current_user(
    authorization: str = Header(...),
    db: DBSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401,"Invalid authorization header format - expected 'Bearer <key>'")
    
    api_key = authorization.removeprefix("Bearer ").strip()
    if not api_key:
        raise HTTPException(401,"Missing API key")
    
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    user = db.query(User).filter(User.api_key_hash == key_hash).first()
    
    if user is None:
        raise HTTPException(401,"Invalid API Key")
    
    return user