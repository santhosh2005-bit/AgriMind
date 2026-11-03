"""FastAPI application entrypoint for AgriMind."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.api import api_router
from backend.app.models.registry import default_registry

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agrimind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown hooks."""
    logger.info("Initializing AgriMind backend services...")
    settings.ensure_directories()

    # Initialize SQLite database schema
    from backend.app.database.db import init_db
    init_db()

    # Log registered models and availability
    profiles = default_registry.list_profiles()
    logger.info(f"Loaded {len(profiles)} model adapters into registry:")
    for p in profiles:
        logger.info(
            f"  - [{p.provider.value}] {p.model_id} (Available: {p.is_available}, Vision: {p.supports_vision})"
        )

    yield

    logger.info("AgriMind backend shut down cleanly.")


app = FastAPI(
    title="AgriMind API",
    description="Reusable Multi-Model, Multimodal, and Agentic AI Agricultural Intelligence System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
app.include_router(api_router, prefix="/api")

# Mount static file endpoints for images and sample demonstration documents
import os
from fastapi.staticfiles import StaticFiles

if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/data/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
if os.path.exists("data/sample_inputs"):
    app.mount("/data/sample_inputs", StaticFiles(directory="data/sample_inputs"), name="sample_inputs")


@app.get("/", tags=["Root"])
def read_root():
    """Root health and discovery endpoint."""
    return {
        "project": "AgriMind",
        "description": "Multi-Model, Multimodal Agentic AI Agricultural Intelligence System",
        "version": "0.1.0",
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "models": "/api/v1/models",
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler to ensure clean JSON error responses."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred during request processing.",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None,
            "path": request.url.path,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
