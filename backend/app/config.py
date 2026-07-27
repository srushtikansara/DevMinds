from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent  # this file's location -> backend/

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    gemini_api_key: str = ""
    devmind_api_key: str = ""
    memory_merge_similarity_threshold: float = 0.92
    apify_api_token: str = ""

    class Config:
        env_file = BASE_DIR / ".env"


settings = Settings()