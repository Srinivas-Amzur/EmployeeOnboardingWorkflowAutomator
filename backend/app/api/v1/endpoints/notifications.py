"""Notification center endpoints."""

from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ....core.security import TokenData
from ....schemas import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from ....services.notification import NotificationService
from ...dependencies import DbSession, get_current_user

router = APIRouter(tags=["notifications"], prefix="/notifications")


def get_notification_service(db: DbSession) -> NotificationService:
    """Resolve notification service dependency."""
    return NotificationService(db)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
) -> NotificationListResponse:
    """List notifications for current user."""
    user_id = UUID(current_user.sub)
    items = await service.list_notifications(user_id=user_id, skip=skip, limit=limit, unread_only=unread_only)
    unread_count = await service.get_unread_count(user_id=user_id)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def unread_notification_count(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> NotificationUnreadCountResponse:
    """Get unread notification badge count."""
    count = await service.get_unread_count(user_id=UUID(current_user.sub))
    return NotificationUnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> NotificationResponse:
    """Mark one notification as read."""
    notification = await service.mark_as_read(user_id=UUID(current_user.sub), notification_id=notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.patch("/read-all", response_model=NotificationMarkAllReadResponse)
async def mark_all_notifications_read(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> NotificationMarkAllReadResponse:
    """Mark all notifications as read for current user."""
    updated = await service.mark_all_as_read(user_id=UUID(current_user.sub))
    return NotificationMarkAllReadResponse(updated=updated)
