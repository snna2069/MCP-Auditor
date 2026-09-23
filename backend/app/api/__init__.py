"""API routers.

Route modules are registered on ``api_router`` here so ``app.main`` only
needs to import a single object.
"""

from fastapi import APIRouter, Depends

from app.api.audits import router as audits_router
from app.api.discovery import router as discovery_router
from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.servers import router as servers_router
from app.core.abuse import enforce_rate_limit
from app.core.auth import require_api_key

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
protected_dependencies = [Depends(require_api_key), Depends(enforce_rate_limit)]
api_router.include_router(servers_router, dependencies=protected_dependencies)
api_router.include_router(discovery_router, dependencies=protected_dependencies)
api_router.include_router(audits_router, dependencies=protected_dependencies)
api_router.include_router(reports_router, dependencies=protected_dependencies)
