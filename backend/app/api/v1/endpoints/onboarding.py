"""
Onboarding workflow endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ....models import Employee, OnboardingTask, OnboardingWorkflow
from ....schemas import (
    OrchestrationEventResponse,
    OrchestrationStateSnapshot,
    OnboardingWorkflowCreate,
    OnboardingWorkflowResponse,
    OnboardingWorkflowUpdate,
    OnboardingTaskCreate,
    OnboardingTaskResponse,
    OnboardingTaskUpdate,
    WorkflowActionRequest,
    WorkflowActionResponse,
)
from ....services.onboarding import OnboardingService
from ....services.orchestration import OrchestrationService
from ....services.employee import EmployeeService
from ...dependencies import DbSession, get_current_user, get_current_admin_user
from ....core.security import TokenData

# Error messages
WORKFLOW_NOT_FOUND = "Workflow not found"
EMPLOYEE_NOT_FOUND = "Employee not found"
TASK_NOT_FOUND = "Task not found"

router = APIRouter(tags=["onboarding"], prefix="/onboarding")


def get_onboarding_service(db: DbSession) -> OnboardingService:
    """Dependency to get onboarding service."""
    return OnboardingService(db)


def get_orchestration_service(db: DbSession) -> OrchestrationService:
    """Dependency to get orchestration read service."""
    return OrchestrationService(db)


def _is_admin_user(current_user: TokenData) -> bool:
    return current_user.role in ["admin", "hr_admin"]


async def _resolve_current_employee_or_404(db: DbSession, current_user: TokenData) -> Employee:
    employee = await EmployeeService(db).get_employee_by_email(current_user.email)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)
    return employee


async def _get_workflow_with_access_or_404(
    db: DbSession,
    workflow_id: UUID,
    current_user: TokenData,
) -> OnboardingWorkflow:
    service = OnboardingService(db)
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=WORKFLOW_NOT_FOUND)

    if not _is_admin_user(current_user):
        employee = await _resolve_current_employee_or_404(db, current_user)
        if workflow.employee_id != employee.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=WORKFLOW_NOT_FOUND)

    return workflow


async def _get_task_with_access_or_404(
    db: DbSession,
    task_id: UUID,
    current_user: TokenData,
) -> OnboardingTask:
    service = OnboardingService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND)

    workflow = await _get_workflow_with_access_or_404(db, task.workflow_id, current_user)
    if workflow.id != task.workflow_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND)

    return task


@router.post(
    "/workflows",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    request: OnboardingWorkflowCreate,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> OnboardingWorkflowResponse:
    """Create new onboarding workflow."""
    service = OnboardingService(db)
    workflow = await service.create_workflow(request)
    return OnboardingWorkflowResponse.model_validate(workflow)


@router.get("/workflows")
async def list_workflows(
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    employee_id: Annotated[UUID | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[OnboardingWorkflowResponse]:
    """List onboarding workflows with optional filtering."""
    service = OnboardingService(db)

    scoped_employee_id = employee_id
    if not _is_admin_user(current_user):
        current_employee = await _resolve_current_employee_or_404(db, current_user)
        scoped_employee_id = current_employee.id

    workflows = await service.get_workflows(
        employee_id=scoped_employee_id,
        skip=skip,
        limit=limit,
    )
    return [OnboardingWorkflowResponse.model_validate(w) for w in workflows]


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> OnboardingWorkflowResponse:
    """Get workflow by ID."""
    workflow = await _get_workflow_with_access_or_404(db, workflow_id, current_user)

    return OnboardingWorkflowResponse.model_validate(workflow)


@router.put("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: UUID,
    request: OnboardingWorkflowUpdate,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> OnboardingWorkflowResponse:
    """Update workflow."""
    service = OnboardingService(db)
    workflow = await service.update_workflow(workflow_id, request)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=WORKFLOW_NOT_FOUND
        )

    return OnboardingWorkflowResponse.model_validate(workflow)


@router.get("/workflows/{workflow_id}/progress")
async def get_workflow_progress(
    workflow_id: UUID,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> dict:
    """Get workflow progress including task statistics."""
    service = OnboardingService(db)
    await _get_workflow_with_access_or_404(db, workflow_id, current_user)
    progress = await service.get_workflow_progress(workflow_id)
    return progress


@router.get(
    "/workflows/{workflow_id}/orchestration",
)
@router.get(
    "/workflows/{workflow_id}/snapshot",
)
async def get_workflow_orchestration_snapshot(
    workflow_id: UUID,
    db: DbSession,
    service: Annotated[OrchestrationService, Depends(get_orchestration_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> OrchestrationStateSnapshot:
    """Get current orchestration state summary for a workflow."""
    await _get_workflow_with_access_or_404(db, workflow_id, current_user)
    snapshot = await service.get_workflow_snapshot(workflow_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WORKFLOW_NOT_FOUND,
        )
    return OrchestrationStateSnapshot.model_validate(snapshot)


@router.post(
    "/workflows/{workflow_id}/actions",
)
async def apply_workflow_action(
    workflow_id: UUID,
    request: WorkflowActionRequest,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> WorkflowActionResponse:
    """Apply lifecycle action (pause/resume/escalate/complete) on a workflow."""
    service = OnboardingService(db)
    workflow, event, message = await service.apply_workflow_action(
        workflow_id=workflow_id,
        action=request.action,
        actor_user_id=UUID(current_user.sub),
        note=request.note,
    )
    if not workflow or not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    return WorkflowActionResponse(
        workflow_id=workflow.id,
        action=request.action,
        current_state=workflow.current_state,
        completion_percentage=workflow.completion_percentage,
        message=message,
        event_id=event.id,
        performed_at=event.created_at,
    )


@router.get(
    "/workflows/{workflow_id}/events",
)
async def get_workflow_orchestration_events(
    workflow_id: UUID,
    db: DbSession,
    service: Annotated[OrchestrationService, Depends(get_orchestration_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> list[OrchestrationEventResponse]:
    """Get orchestration audit events for a workflow."""
    await _get_workflow_with_access_or_404(db, workflow_id, current_user)
    events = await service.get_workflow_events(workflow_id)
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WORKFLOW_NOT_FOUND,
        )
    return [OrchestrationEventResponse.model_validate(event) for event in events]


@router.post(
    "/workflows/{workflow_id}/tasks",
    status_code=status.HTTP_201_CREATED,
)
async def add_task(
    workflow_id: UUID,
    request: OnboardingTaskCreate,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> OnboardingTaskResponse:
    """Add a task to a workflow."""
    service = OnboardingService(db)

    # Verify workflow exists
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=WORKFLOW_NOT_FOUND
        )

    # Verify workflow_id matches
    if request.workflow_id != workflow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow ID mismatch",
        )

    task = await service.create_task(request)
    return OnboardingTaskResponse.model_validate(task)


@router.get("/workflows/{workflow_id}/tasks")
async def get_workflow_tasks(
    workflow_id: UUID,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[OnboardingTaskResponse]:
    """Get all tasks for a workflow."""
    service = OnboardingService(db)

    await _get_workflow_with_access_or_404(db, workflow_id, current_user)

    tasks = await service.get_workflow_tasks(workflow_id, skip=skip, limit=limit)
    return [OnboardingTaskResponse.model_validate(t) for t in tasks]


@router.patch(
    "/tasks/{task_id}",
    responses={status.HTTP_404_NOT_FOUND: {"description": TASK_NOT_FOUND}},
)
async def update_task(
    task_id: UUID,
    request: OnboardingTaskUpdate,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> OnboardingTaskResponse:
    """Update a task (partial update)."""
    service = OnboardingService(db)
    await _get_task_with_access_or_404(db, task_id, current_user)
    task = await service.update_task(task_id, request)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TASK_NOT_FOUND)
    return OnboardingTaskResponse.model_validate(task)


@router.get("/employees/{employee_id}/summary")
async def get_employee_onboarding_summary(
    employee_id: UUID,
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> dict:
    """Get complete onboarding summary for an employee."""
    if not _is_admin_user(current_user):
        current_employee = await _resolve_current_employee_or_404(db, current_user)
        if current_employee.id != employee_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)

    service = OnboardingService(db)
    summary = await service.get_employee_onboarding_summary(employee_id)
    return summary
