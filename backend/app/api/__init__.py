"""API routers.

Route modules are registered on ``api_router`` here so ``app.main`` only
needs to import a single object.
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.servers import router as servers_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(servers_router)
