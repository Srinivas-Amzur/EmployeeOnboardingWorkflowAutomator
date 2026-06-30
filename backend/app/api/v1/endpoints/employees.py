"""
Employee endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ....schemas import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from ....services.employee import EmployeeService
from ...dependencies import DbSession, get_current_user, get_current_admin_user
from ....core.security import TokenData

router = APIRouter(tags=["employees"], prefix="/employees")
EMPLOYEE_NOT_FOUND = "Employee not found"


def _is_admin_user(current_user: TokenData) -> bool:
    return current_user.role in ["admin", "hr_admin"]


def get_employee_service(db: DbSession) -> EmployeeService:
    """Dependency to get the employee service."""
    return EmployeeService(db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_employee(
    request: EmployeeCreate,
    service: Annotated[EmployeeService, Depends(get_employee_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> EmployeeResponse:
    """Create a new employee."""
    employee = await service.create_employee(request)
    return EmployeeResponse.model_validate(employee)


@router.get("/me")
async def get_my_employee_profile(
    service: Annotated[EmployeeService, Depends(get_employee_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> EmployeeResponse:
    """Get employee profile mapped to the authenticated user email."""
    employee = await service.get_employee_by_email(current_user.email)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)
    return EmployeeResponse.model_validate(employee)


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    service: Annotated[EmployeeService, Depends(get_employee_service)],
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> EmployeeResponse:
    """Get employee by ID."""
    employee = await service.get_employee(employee_id)

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)

    if not _is_admin_user(current_user) and employee.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)

    return EmployeeResponse.model_validate(employee)


@router.get("")
async def list_employees(
    service: Annotated[EmployeeService, Depends(get_employee_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
    skip: int = 0,
    limit: int = 100,
) -> list[EmployeeResponse]:
    """List all employees."""
    employees = await service.list_employees(skip=skip, limit=limit)
    return [EmployeeResponse.model_validate(e) for e in employees]


@router.put("/{employee_id}")
async def update_employee(
    employee_id: str,
    request: EmployeeUpdate,
    service: Annotated[EmployeeService, Depends(get_employee_service)],
    current_user: Annotated[TokenData, Depends(get_current_admin_user)],
) -> EmployeeResponse:
    """Update employee."""
    employee = await service.update_employee(employee_id, request)

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EMPLOYEE_NOT_FOUND)

    return EmployeeResponse.model_validate(employee)
