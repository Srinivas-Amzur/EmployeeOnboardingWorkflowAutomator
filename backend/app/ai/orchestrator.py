"""LangGraph workflow definition for onboarding orchestration."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

WORKFLOW_STATES = [
    "initiated",
    "hr_review",
    "provisioning",
    "meetings_scheduled",
    "documents_shared",
    "completed",
]

DEFAULT_TASK_BLUEPRINTS: dict[str, list[dict[str, Any]]] = {
    "hr_review": [
        {"title": "Validate employee information", "description": "Review submitted employee profile and joining details.", "priority": "high", "offset_days": -7},
        {"title": "Verify joining date", "description": "Confirm the joining date with HR and hiring manager.", "priority": "medium", "offset_days": -6},
        {"title": "Assign onboarding owner", "description": "Assign a responsible HR owner for the onboarding workflow.", "priority": "medium", "offset_days": -6},
    ],
    "provisioning": [
        {"title": "Create email account", "description": "Provision corporate email account.", "priority": "high", "offset_days": -5},
        {"title": "Provision Slack", "description": "Grant Slack workspace access.", "priority": "medium", "offset_days": -5},
        {"title": "Assign GitHub access", "description": "Grant GitHub organization access.", "priority": "high", "offset_days": -4},
        {"title": "Configure VPN", "description": "Provision secure VPN access.", "priority": "high", "offset_days": -4},
        {"title": "Allocate hardware", "description": "Reserve and assign laptop and accessories.", "priority": "high", "offset_days": -3},
    ],
    "meetings_scheduled": [
        {"title": "Schedule HR orientation", "description": "Book HR orientation meeting.", "priority": "medium", "offset_days": -2},
        {"title": "Schedule manager introduction", "description": "Book intro with manager.", "priority": "medium", "offset_days": -1},
        {"title": "Schedule team onboarding", "description": "Coordinate first team onboarding session.", "priority": "medium", "offset_days": -1},
    ],
    "documents_shared": [
        {"title": "Share employee handbook", "description": "Send handbook and onboarding guide.", "priority": "medium", "offset_days": 0},
        {"title": "Share NDA and policy pack", "description": "Provide NDA, policies, and compliance documents.", "priority": "high", "offset_days": 0},
    ],
}


class OnboardingGraphState(TypedDict):
    """State used by the onboarding LangGraph pipeline."""

    employee_id: str
    employee_name: str
    employee_email: str
    manager_id: str | None
    joining_date: str
    workflow_id: str
    current_state: str
    completion_percentage: int
    is_new_workflow: bool
    existing_tasks: list[dict[str, Any]]
    task_blueprints: list[dict[str, Any]]
    notifications: list[dict[str, str]]
    events: list[dict[str, Any]]
    escalations: list[dict[str, Any]]
    errors: list[str]


def _route_initialize(state: OnboardingGraphState) -> str:
    return "generate_tasks" if not state["errors"] else "end"


def _route_generate(state: OnboardingGraphState) -> str:
    return "provisioning_tasks" if not state["errors"] else "end"


def _route_provisioning(state: OnboardingGraphState) -> str:
    return "schedule_meetings" if not state["errors"] else "end"


def _route_schedule(state: OnboardingGraphState) -> str:
    return "share_documents" if not state["errors"] else "end"


def _route_share(state: OnboardingGraphState) -> str:
    return "complete_workflow" if not state["errors"] else "end"


def _route_complete(state: OnboardingGraphState) -> str:
    return "end"


def _configure_workflow_edges(workflow: StateGraph) -> None:
    workflow.set_entry_point("initialize_workflow")
    workflow.add_conditional_edges("initialize_workflow", _route_initialize, {"generate_tasks": "generate_tasks", "end": END})
    workflow.add_conditional_edges("generate_tasks", _route_generate, {"provisioning_tasks": "provisioning_tasks", "end": END})
    workflow.add_conditional_edges("provisioning_tasks", _route_provisioning, {"schedule_meetings": "schedule_meetings", "end": END})
    workflow.add_conditional_edges("schedule_meetings", _route_schedule, {"share_documents": "share_documents", "end": END})
    workflow.add_conditional_edges("share_documents", _route_share, {"complete_workflow": "complete_workflow", "end": END})
    workflow.add_conditional_edges("complete_workflow", _route_complete, {"end": END})


def create_onboarding_orchestrator():
    """Build and compile the deterministic LangGraph workflow."""

    def initialize_workflow(state: OnboardingGraphState) -> OnboardingGraphState:
        new_state = dict(state)
        new_state["current_state"] = new_state.get("current_state") or "initiated"
        if new_state["is_new_workflow"] and new_state["current_state"] == "initiated" and not new_state["existing_tasks"]:
            new_state["events"] = [
                {
                    "event_type": "workflow_started",
                    "status": "success",
                    "state_from": None,
                    "state_to": "initiated",
                    "message": f"Onboarding workflow started for {new_state['employee_name']}",
                    "payload": {"workflow_id": new_state["workflow_id"]},
                }
            ]
            new_state["notifications"] = [
                {
                    "event_type": "workflow_started",
                    "title": "Workflow started",
                    "message": f"Your onboarding workflow has started, {new_state['employee_name']}.",
                }
            ]
        return new_state

    def generate_tasks(state: OnboardingGraphState) -> OnboardingGraphState:
        return _append_stage_tasks(state, "hr_review", "HR review tasks generated")

    def provisioning_tasks(state: OnboardingGraphState) -> OnboardingGraphState:
        return _append_stage_tasks(state, "provisioning", "Provisioning tasks generated")

    def schedule_meetings(state: OnboardingGraphState) -> OnboardingGraphState:
        return _append_stage_tasks(state, "meetings_scheduled", "Meeting scheduling tasks generated")

    def share_documents(state: OnboardingGraphState) -> OnboardingGraphState:
        return _append_stage_tasks(state, "documents_shared", "Document-sharing tasks generated")

    def complete_workflow(state: OnboardingGraphState) -> OnboardingGraphState:
        new_state = dict(state)
        all_tasks = list(new_state["existing_tasks"]) + list(new_state["task_blueprints"])
        next_state = _derive_current_state(all_tasks)
        completion_percentage = _calculate_completion_percentage(all_tasks)

        state_from = new_state.get("current_state")
        new_state["current_state"] = next_state
        new_state["completion_percentage"] = completion_percentage
        new_state["escalations"] = _build_escalations(all_tasks, new_state["workflow_id"], new_state["employee_name"])

        if state_from != next_state:
            new_state["events"].append(
                {
                    "event_type": "workflow_state_changed",
                    "status": "success",
                    "state_from": state_from,
                    "state_to": next_state,
                    "message": f"Workflow advanced from {state_from} to {next_state}",
                    "payload": {"completion_percentage": completion_percentage},
                }
            )

        if next_state == "completed":
            new_state["notifications"].append(
                {
                    "event_type": "workflow_completed",
                    "title": "Onboarding completed",
                    "message": f"Onboarding completed for {new_state['employee_name']}.",
                }
            )
            new_state["events"].append(
                {
                    "event_type": "workflow_completed",
                    "status": "success",
                    "state_from": state_from,
                    "state_to": "completed",
                    "message": f"Workflow completed for {new_state['employee_name']}",
                    "payload": {"workflow_id": new_state["workflow_id"]},
                }
            )

        return new_state

    workflow = StateGraph(OnboardingGraphState)
    workflow.add_node("initialize_workflow", initialize_workflow)
    workflow.add_node("generate_tasks", generate_tasks)
    workflow.add_node("provisioning_tasks", provisioning_tasks)
    workflow.add_node("schedule_meetings", schedule_meetings)
    workflow.add_node("share_documents", share_documents)
    workflow.add_node("complete_workflow", complete_workflow)

    _configure_workflow_edges(workflow)

    return workflow.compile()


def _append_stage_tasks(
    state: OnboardingGraphState,
    stage: str,
    event_message: str,
) -> OnboardingGraphState:
    new_state = dict(state)
    existing_keys = {(task["stage"], task["title"]) for task in new_state["existing_tasks"] + new_state["task_blueprints"]}
    joining_date = date.fromisoformat(new_state["joining_date"])
    added_titles: list[str] = []

    for template in DEFAULT_TASK_BLUEPRINTS[stage]:
        key = (stage, template["title"])
        if key in existing_keys:
            continue

        due_date = _normalize_due_date(joining_date, template["offset_days"])
        new_state["task_blueprints"].append(
            {
                "stage": stage,
                "title": template["title"],
                "description": template["description"],
                "priority": template["priority"],
                "status": "pending",
                "due_date": due_date.isoformat(),
                "assigned_to": new_state["manager_id"] if stage == "hr_review" else None,
            }
        )
        added_titles.append(template["title"])

    if added_titles:
        new_state["events"].append(
            {
                "event_type": "tasks_generated",
                "status": "success",
                "state_from": new_state["current_state"],
                "state_to": stage,
                "message": event_message,
                "payload": {"stage": stage, "titles": added_titles},
            }
        )
        new_state["notifications"].append(
            {
                "event_type": "tasks_assigned",
                "title": "Tasks assigned",
                "message": f"{len(added_titles)} {stage.replace('_', ' ')} tasks were created.",
            }
        )

    return new_state


def _calculate_completion_percentage(tasks: list[dict[str, Any]]) -> int:
    if not tasks:
        return 0
    completed = sum(1 for task in tasks if task.get("status") == "completed")
    return int((completed / len(tasks)) * 100)


def _derive_current_state(tasks: list[dict[str, Any]]) -> str:
    if not tasks:
        return "initiated"

    for stage in ["hr_review", "provisioning", "meetings_scheduled", "documents_shared"]:
        stage_tasks = [task for task in tasks if task.get("stage") == stage]
        if stage_tasks and any(task.get("status") != "completed" for task in stage_tasks):
            return stage
    return "completed"


def _build_escalations(
    tasks: list[dict[str, Any]],
    workflow_id: str,
    employee_name: str,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    escalations: list[dict[str, Any]] = []
    for task in tasks:
        due_date = task.get("due_date")
        if not due_date or task.get("status") == "completed":
            continue
        due_at = _ensure_aware_datetime(datetime.fromisoformat(due_date))
        if due_at + timedelta(hours=24) < now:
            escalations.append(
                {
                    "event_type": "escalation",
                    "status": "warning",
                    "state_from": task.get("stage"),
                    "state_to": task.get("stage"),
                    "message": f"Escalation triggered for overdue task '{task['title']}' in workflow {workflow_id}",
                    "payload": {"task_title": task["title"], "employee_name": employee_name},
                }
            )
    return escalations


def _ensure_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _normalize_due_date(joining_date: date, offset_days: int) -> datetime:
    due_date = max(date.today(), joining_date + timedelta(days=offset_days))
    return datetime.combine(due_date, time(hour=17, minute=0), tzinfo=timezone.utc)
