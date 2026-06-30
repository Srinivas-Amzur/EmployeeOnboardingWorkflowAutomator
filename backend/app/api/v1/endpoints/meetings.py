"""Meeting endpoints for onboarding calendar MVP."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ....core.security import TokenData
from ....models import OnboardingWorkflow
from ....schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate, ScheduleMeetingRequest
from ....services.employee import EmployeeService
from ....services.meeting import MeetingService
from ...dependencies import DbSession, get_current_admin_user, get_current_user

router = APIRouter(tags=["meetings"], prefix="/meetings")
MEETING_NOT_FOUND = "Meeting not found"


def get_meeting_service(db: DbSession) -> MeetingService:
    """Dependency to build meeting service."""
    return MeetingService(db)


def _is_admin_user(current_user: TokenData) -> bool:
    return current_user.role in ["admin", "hr_admin"]


async def _resolve_current_employee_id(db: DbSession, current_user: TokenData) -> UUID:
    employee = await EmployeeService(db).get_employee_by_email(current_user.email)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee.id


async def _ensure_workflow_access(
    db: DbSession,
    workflow_id: UUID,
    current_user: TokenData,
) -> None:
    if _is_admin_user(current_user):
        return

    employee_id = await _resolve_current_employee_id(db, current_user)
    workflow = await db.get(OnboardingWorkflow, workflow_id)
    if not workflow or workflow.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_meeting(
    request: MeetingCreate,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> MeetingResponse:
    """Create an onboarding meeting."""
    meeting = await service.create_meeting(request, actor_user_id=UUID(current_user.sub))
    return MeetingResponse.model_validate(meeting)


@router.get("")
async def list_meetings(
    db: DbSession,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
    employee_id: Annotated[UUID | None, Query()] = None,
    workflow_id: Annotated[UUID | None, Query()] = None,
    upcoming_only: Annotated[bool, Query()] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[MeetingResponse]:
    """List meetings with optional employee/workflow filters."""
    scoped_employee_id = employee_id
    if not _is_admin_user(current_user):
        scoped_employee_id = await _resolve_current_employee_id(db, current_user)

    if workflow_id:
        await _ensure_workflow_access(db, workflow_id, current_user)

    meetings = await service.list_meetings(
        employee_id=scoped_employee_id,
        workflow_id=workflow_id,
        upcoming_only=upcoming_only,
        skip=skip,
        limit=limit,
    )
    return [MeetingResponse.model_validate(item) for item in meetings]


@router.get("/{meeting_id}")
async def get_meeting(
    meeting_id: UUID,
    db: DbSession,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> MeetingResponse:
    """Get one meeting by ID."""
    meeting = await service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MEETING_NOT_FOUND)

    if not _is_admin_user(current_user):
        employee_id = await _resolve_current_employee_id(db, current_user)
        if meeting.employee_id != employee_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MEETING_NOT_FOUND)

    return MeetingResponse.model_validate(meeting)


@router.put("/{meeting_id}")
async def update_meeting(
    meeting_id: UUID,
    request: MeetingUpdate,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> MeetingResponse:
    """Update one meeting."""
    meeting = await service.update_meeting(meeting_id, request, actor_user_id=UUID(current_user.sub))
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MEETING_NOT_FOUND)
    return MeetingResponse.model_validate(meeting)


@router.delete("/{meeting_id}", status_code=status.HTTP_200_OK)
async def delete_meeting(
    meeting_id: UUID,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> None:
    """Delete one meeting."""
    removed = await service.delete_meeting(meeting_id, actor_user_id=UUID(current_user.sub))
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MEETING_NOT_FOUND)


@router.post("/workflows/{workflow_id}/schedule-orientation")
async def schedule_orientation_meeting(
    workflow_id: UUID,
    request: ScheduleMeetingRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> MeetingResponse:
    """Schedule orientation meeting for workflow."""
    try:
        meeting = await service.schedule_orientation_meeting(
            workflow_id=workflow_id,
            actor_user_id=UUID(current_user.sub),
            scheduled_for=request.scheduled_for,
            duration_minutes=request.duration_minutes,
            location=request.location,
            meeting_url=request.meeting_url,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MeetingResponse.model_validate(meeting)


@router.post("/workflows/{workflow_id}/schedule-manager-introduction")
async def schedule_manager_introduction(
    workflow_id: UUID,
    request: ScheduleMeetingRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> MeetingResponse:
    """Schedule manager introduction for workflow."""
    try:
        meeting = await service.schedule_manager_introduction(
            workflow_id=workflow_id,
            actor_user_id=UUID(current_user.sub),
            scheduled_for=request.scheduled_for,
            duration_minutes=request.duration_minutes,
            location=request.location,
            meeting_url=request.meeting_url,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MeetingResponse.model_validate(meeting)


@router.post("/workflows/{workflow_id}/schedule-team-onboarding-session")
async def schedule_team_onboarding_session(
    workflow_id: UUID,
    request: ScheduleMeetingRequest,
    service: Annotated[MeetingService, Depends(get_meeting_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> MeetingResponse:
    """Schedule team onboarding session for workflow."""
    try:
        meeting = await service.schedule_team_onboarding_session(
            workflow_id=workflow_id,
            actor_user_id=UUID(current_user.sub),
            scheduled_for=request.scheduled_for,
            duration_minutes=request.duration_minutes,
            location=request.location,
            meeting_url=request.meeting_url,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MeetingResponse.model_validate(meeting)
