"""Audit log schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    """Normalized audit item for UI timelines and exports."""

    timestamp: datetime
    user: str
    action: str
    entity: str
    entity_id: str
    details: str = Field(default="")


class AuditLogListResponse(BaseModel):
    """Audit log list response with total and paginated items."""

    items: list[AuditLogItem]
    total: int = Field(ge=0)