from fastapi import APIRouter, Depends

from app.api.routes import analyses, auth, chat, documents, health, startups, surrounding
from app.core.auth import get_current_user

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(startups.router, prefix="/startups", tags=["startups"])
api_router.include_router(documents.router, prefix="/startups", tags=["documents"])
api_router.include_router(analyses.router, prefix="/startups", tags=["analyses"])
api_router.include_router(chat.router, prefix="/startups", tags=["chat"])
# Surrounding-area helper endpoints (geocode gate + map POIs); owned by the module.
api_router.include_router(
    surrounding.router,
    tags=["surrounding_area"],
    dependencies=[Depends(get_current_user)],
)
