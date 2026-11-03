"""API routing package exports."""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.models import router as models_router
from backend.app.api.routing import router as routing_router
from backend.app.api.workflow import router as workflow_router
from backend.app.api.tools import router as tools_router
from backend.app.api.ingestion import router as ingestion_router
from backend.app.api.traces import router as traces_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(routing_router)
api_router.include_router(workflow_router)
api_router.include_router(tools_router)
api_router.include_router(ingestion_router)
api_router.include_router(traces_router)

__all__ = [
    "api_router",
    "health_router",
    "models_router",
    "routing_router",
    "workflow_router",
    "tools_router",
    "ingestion_router",
    "traces_router",
]
