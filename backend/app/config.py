from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url:str
    redis_url: str = "redis://localhost:6379/0"
    gemini_api_key: str = ""
    class Config:
        env_file = ".env"
settings = Settings()