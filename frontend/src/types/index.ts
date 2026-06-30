export interface User {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Employee {
  id: string
  first_name: string
  last_name: string
  email: string
  company_email?: string | null
  department: string
  designation: string
  manager_id: string | null
  joining_date: string
  onboarding_status: string
  created_at: string
  updated_at: string
}

export interface OnboardingTask {
  id: string
  workflow_id: string
  title: string
  description: string | null
  assigned_to: string | null
  status: string
  priority: string
  due_date: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface OnboardingWorkflow {
  id: string
  employee_id: string
  current_state: string
  completion_percentage: number
  started_at: string
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface OnboardingMeeting {
  id: string
  employee_id: string
  workflow_id: string
  created_by: string | null
  meeting_type: "orientation" | "manager_introduction" | "team_onboarding" | "custom"
  title: string
  description: string | null
  scheduled_for: string
  duration_minutes: number
  location: string | null
  meeting_url: string | null
  status: "scheduled" | "completed" | "cancelled"
  created_at: string
  updated_at: string
}

export interface ScheduleMeetingPayload {
  scheduled_for?: string
  duration_minutes?: number
  location?: string
  meeting_url?: string
  note?: string
}

export interface WorkflowActionResponse {
  workflow_id: string
  action: "pause" | "resume" | "escalate" | "complete"
  current_state: string
  completion_percentage: number
  message: string
  event_id: string
  performed_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  name: string
  email: string
  password: string
  role?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface MessageResponse {
  message: string
}

export interface ToastMessage {
  id: string
  title: string
  description?: string
  variant?: "success" | "error" | "info"
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

export type WorkflowState =
  | "initiated"
  | "hr_review"
  | "provisioning"
  | "meetings_scheduled"
  | "documents_shared"
  | "completed"

export type TaskStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "blocked"

export type TaskPriority =
  | "low"
  | "medium"
  | "high"
  | "urgent"

export interface RagSourceReference {
  index: number
  document_id: string | null
  document_name: string
  document_type: string
  chunk_index: number
  score: number
  excerpt: string
  file_name: string | null
}

export interface RagChatRequest {
  question: string
  top_k?: number
  session_id?: string | null
}

export interface RagChatResponse {
  answer: string
  session_id: string
  retrieved_chunks: number
  sources: RagSourceReference[]
}

export interface RagDocument {
  document_id: string
  document_name: string
  document_type: string
  file_path?: string | null
  chunks_indexed?: number | null
  file_size?: number | null
  ingested_at?: string | null
}

export type NotificationType =
  | "workflow_started"
  | "onboarding_approved"
  | "provisioning_started"
  | "workflow_transition"
  | "task_assigned"
  | "task_completed"
  | "onboarding_completed"
  | "ai_orchestration"
  | "ai_indexing_completed"
  | "escalation"

export interface NotificationItem {
  id: string
  user_id: string
  notification_type: NotificationType
  title: string
  message: string
  is_read: boolean
  read_at: string | null
  payload?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  unread_count: number
}

export interface NotificationUnreadCountResponse {
  count: number
}

export interface AuditLogItem {
  timestamp: string
  user: string
  action: string
  entity: string
  entity_id: string
  details: string
}

export interface AuditLogListResponse {
  items: AuditLogItem[]
  total: number
}
