from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) # Allow CORS for frontend development

app.include_router(health.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Movie Agent API", 
        "docs": "/docs", 
        "health": "/health", 
    }