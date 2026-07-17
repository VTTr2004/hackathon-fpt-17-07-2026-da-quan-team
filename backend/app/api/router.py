from fastapi import APIRouter

from app.api.routes import analyses, chat, documents, health, startups

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(startups.router, prefix="/startups", tags=["startups"])
api_router.include_router(documents.router, prefix="/startups", tags=["documents"])
api_router.include_router(analyses.router, prefix="/startups", tags=["analyses"])
api_router.include_router(chat.router, prefix="/startups", tags=["chat"])
