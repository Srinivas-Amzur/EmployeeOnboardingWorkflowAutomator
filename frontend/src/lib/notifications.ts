import type { NotificationType } from "../types"

export type NotificationSeverity = "info" | "success" | "warning" | "error"

export function getNotificationSeverity(type: NotificationType | string): NotificationSeverity {
  if (type.includes("escalation") || type.includes("failed") || type.includes("error")) return "error"
  if (type.includes("warning") || type.includes("overdue")) return "warning"
  if (type.includes("completed") || type.includes("success")) return "success"
  return "info"
}

export function getNotificationIcon(type: NotificationType | string): string {
  if (type.includes("workflow_started") || type.includes("started")) return "🚀"
  if (type.includes("task_assigned") || type.includes("task")) return "📋"
  if (type.includes("ai_index") || type.includes("index") || type.includes("ai_orchestration")) return "🤖"
  if (type.includes("onboarding_completed") || type.includes("completed")) return "✅"
  if (type.includes("escalation") || type.includes("warning") || type.includes("overdue")) return "⚠️"
  return "🔔"
}

export function getNotificationCategory(type: NotificationType | string): "workflow" | "tasks" | "ai" | "escalations" {
  if (type.includes("escalation") || type.includes("overdue")) return "escalations"
  if (type.includes("ai") || type.includes("index")) return "ai"
  if (type.includes("task")) return "tasks"
  return "workflow"
}
