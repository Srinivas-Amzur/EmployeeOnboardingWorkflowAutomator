"""Audit log endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ....core.security import TokenData
from ....schemas import AuditLogItem, AuditLogListResponse
from ....services.audit import AuditService
from ...dependencies import DbSession, get_current_user

router = APIRouter(tags=["audit"], prefix="/audit")


def get_audit_service(db: DbSession) -> AuditService:
    """Resolve audit service dependency."""
    return AuditService(db)


@router.get("/logs")
async def list_audit_logs(
    service: Annotated[AuditService, Depends(get_audit_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> AuditLogListResponse:
    """List cross-entity audit logs ordered by newest first."""
    payload = await service.list_logs(
        viewer_user_id=current_user.sub,
        viewer_email=current_user.email,
        viewer_role=current_user.role,
        skip=skip,
        limit=limit,
    )
    return AuditLogListResponse(
        items=[AuditLogItem(**item) for item in payload["items"]],
        total=payload["total"],
    )