"""
Main FastAPI application factory.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .core.logging import setup_logging
from .api.v1 import api_router
from .db.session import get_db_health, log_startup_db_diagnostics, retry_warmup_connection
from .middleware.error_handler import ErrorHandlingMiddleware, RequestLoggingMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    setup_logging()
    from .db.session import engine

    await log_startup_db_diagnostics()

    # Pre-warm the connection pool so first requests avoid connection races.
    try:
        success = await retry_warmup_connection(attempt=0, max_retries=5)
        if success:
            logger.info("Database connection pool warmed up successfully.")
        else:
            logger.warning("DB warm-up retries exhausted. API is running but DB is currently unreachable.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB warm-up failed (will retry on first request): %s", exc)

    yield

    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Error handling middleware (added first, runs last)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/health/db")
    async def health_check_db() -> JSONResponse:
        """Database health endpoint with diagnostics."""
        payload = await get_db_health()
        status_code = status.HTTP_200_OK if payload.get("connected") else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(content=payload, status_code=status_code)

    return app


# Create the app instance for uvicorn
app = create_app()
