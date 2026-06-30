"""API v1 endpoints."""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.audit import router as audit_router
from .endpoints.employees import router as employees_router
from .endpoints.meetings import router as meetings_router
from .endpoints.onboarding import router as onboarding_router
from .endpoints.notifications import router as notifications_router
from .endpoints.rag import router as rag_router
from .endpoints.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(audit_router)
api_router.include_router(employees_router)
api_router.include_router(meetings_router)
api_router.include_router(onboarding_router)
api_router.include_router(notifications_router)
api_router.include_router(rag_router)
api_router.include_router(analytics_router)

__all__ = ["api_router"]
