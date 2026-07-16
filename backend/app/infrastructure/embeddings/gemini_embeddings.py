from google import genai
from app.config import settings


client = genai.Client(api_key=settings.gemini_api_key)
def get_embedding(text:str,task_type:str="RETRIEVAL_DOCUMENT") -> list[float]:
    """Convert text into vectors (list of numbers) represting its meaning"""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents= text,
        config={
            "task_type":task_type,
            "output_dimensionality":768,
        },
    )
    return result.embeddings[0].values