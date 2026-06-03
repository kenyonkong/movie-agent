from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, recommend, feedback
from app.core.config import settings
from app.db import models
from app.db.database import create_db_tables

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

create_db_tables() # Create database tables at startup

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
app.include_router(recommend.router)
app.include_router(feedback.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Movie Agent API", 
        "docs": "/docs", 
        "health": "/health", 
        "recommend": "/recommend",
        "feedback": "/feedback"
    }