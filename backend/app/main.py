from fastapi import FastAPI

from app.interfaces.http.router import router

app = FastAPI(title="DevMind API", version="0.1.0")

app.include_router(router, prefix="/api/v1")