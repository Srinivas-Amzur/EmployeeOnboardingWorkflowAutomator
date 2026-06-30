import axios, { AxiosInstance } from "axios"
import type {
  AuditLogListResponse,
  ChangePasswordRequest,
  Employee,
  LoginCredentials,
  MessageResponse,
  NotificationItem,
  NotificationListResponse,
  NotificationUnreadCountResponse,
  OnboardingMeeting,
  OnboardingTask,
  OnboardingWorkflow,
  RagChatRequest,
  RagChatResponse,
  RagDocument,
  RegisterCredentials,
  ScheduleMeetingPayload,
  User,
  WorkflowActionResponse,
} from "../types"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"

const client: AxiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true,
})

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials) => {
    const response = await client.post("/auth/login", credentials)
    return response.data
  },

  googleLogin: async (idToken: string) => {
    const response = await client.post("/auth/google", { id_token: idToken })
    return response.data
  },

  me: async () => {
    const response = await client.get("/auth/me")
    return response.data as User
  },

  logout: async () => {
    const response = await client.post("/auth/logout")
    return response.data as MessageResponse
  },

  register: async (data: RegisterCredentials) => {
    const response = await client.post("/auth/register", data)
    return response.data
  },

  changePassword: async (data: ChangePasswordRequest) => {
    const response = await client.patch("/auth/change-password", data)
    return response.data as MessageResponse
  },
}

// Employee API
export const employeeAPI = {
  create: async (data: Omit<Employee, "id" | "onboarding_status" | "created_at" | "updated_at">) => {
    const response = await client.post("/employees", data)
    return response.data as Employee
  },

  get: async (id: string) => {
    const response = await client.get(`/employees/${id}`)
    return response.data as Employee
  },

  me: async () => {
    const response = await client.get("/employees/me")
    return response.data as Employee
  },

  list: async (skip = 0, limit = 100) => {
    const response = await client.get("/employees", { params: { skip, limit } })
    return response.data as Employee[]
  },

  update: async (id: string, data: Partial<Employee>) => {
    const response = await client.put(`/employees/${id}`, data)
    return response.data as Employee
  },
}

// Onboarding API
export const onboardingAPI = {
  createWorkflow: async (data: { employee_id: string; current_state?: string }) => {
    const response = await client.post("/onboarding/workflows", data)
    return response.data as OnboardingWorkflow
  },

  listWorkflows: async (params: { employee_id?: string; skip?: number; limit?: number } = {}) => {
    const response = await client.get("/onboarding/workflows", { params })
    return response.data as OnboardingWorkflow[]
  },

  getWorkflow: async (id: string) => {
    const response = await client.get(`/onboarding/workflows/${id}`)
    return response.data as OnboardingWorkflow
  },

  updateWorkflow: async (id: string, data: Partial<OnboardingWorkflow>) => {
    const response = await client.put(`/onboarding/workflows/${id}`, data)
    return response.data as OnboardingWorkflow
  },

  getWorkflowProgress: async (id: string) => {
    const response = await client.get(`/onboarding/workflows/${id}/progress`)
    return response.data
  },

  getWorkflowSnapshot: async (id: string) => {
    const response = await client.get(`/onboarding/workflows/${id}/snapshot`)
    return response.data as {
      workflow_id: string
      current_state: string
      completion_percentage: number
      open_tasks: number
      overdue_tasks: number
      blocked_tasks: number
      escalations: number
      synced_at: string
    }
  },

  getWorkflowEvents: async (id: string, limit = 50) => {
    const response = await client.get(`/onboarding/workflows/${id}/events`, { params: { limit } })
    return response.data as Array<{
      id: string
      event_type: string
      status: string
      state_from: string | null
      state_to: string | null
      message: string
      created_at: string
    }>
  },

  getWorkflowTasks: async (workflowId: string, params: { skip?: number; limit?: number } = {}) => {
    const response = await client.get(`/onboarding/workflows/${workflowId}/tasks`, { params })
    return response.data as OnboardingTask[]
  },

  addTask: async (workflowId: string, data: Partial<OnboardingTask> & { title: string }) => {
    const response = await client.post(`/onboarding/workflows/${workflowId}/tasks`, {
      ...data,
      workflow_id: workflowId,
    })
    return response.data as OnboardingTask
  },

  updateTask: async (taskId: string, data: Partial<OnboardingTask>) => {
    const response = await client.patch(`/onboarding/tasks/${taskId}`, data)
    return response.data as OnboardingTask
  },

  getEmployeeSummary: async (employeeId: string) => {
    const response = await client.get(`/onboarding/employees/${employeeId}/summary`)
    return response.data
  },

  applyWorkflowAction: async (
    workflowId: string,
    action: "pause" | "resume" | "escalate" | "complete",
    note?: string,
  ) => {
    const response = await client.post(`/onboarding/workflows/${workflowId}/actions`, { action, note })
    return response.data as WorkflowActionResponse
  },
}

export const meetingAPI = {
  list: async (params: {
    employee_id?: string
    workflow_id?: string
    upcoming_only?: boolean
    skip?: number
    limit?: number
  } = {}) => {
    const response = await client.get("/meetings", { params })
    return response.data as OnboardingMeeting[]
  },

  get: async (meetingId: string) => {
    const response = await client.get(`/meetings/${meetingId}`)
    return response.data as OnboardingMeeting
  },

  create: async (data: Omit<OnboardingMeeting, "id" | "created_at" | "updated_at" | "created_by">) => {
    const response = await client.post("/meetings", data)
    return response.data as OnboardingMeeting
  },

  update: async (meetingId: string, data: Partial<OnboardingMeeting>) => {
    const response = await client.put(`/meetings/${meetingId}`, data)
    return response.data as OnboardingMeeting
  },

  remove: async (meetingId: string) => {
    await client.delete(`/meetings/${meetingId}`)
  },

  scheduleOrientation: async (workflowId: string, data: ScheduleMeetingPayload = {}) => {
    const response = await client.post(`/meetings/workflows/${workflowId}/schedule-orientation`, data)
    return response.data as OnboardingMeeting
  },

  scheduleManagerIntroduction: async (workflowId: string, data: ScheduleMeetingPayload = {}) => {
    const response = await client.post(`/meetings/workflows/${workflowId}/schedule-manager-introduction`, data)
    return response.data as OnboardingMeeting
  },

  scheduleTeamOnboardingSession: async (workflowId: string, data: ScheduleMeetingPayload = {}) => {
    const response = await client.post(`/meetings/workflows/${workflowId}/schedule-team-onboarding-session`, data)
    return response.data as OnboardingMeeting
  },
}

// Analytics API
export const analyticsAPI = {
  getDashboardStats: async () => {
    const response = await client.get("/analytics/dashboard")
    return response.data
  },

  exportReport: async (
    reportType: "workflow" | "employee" | "audit",
    format: "csv" | "pdf",
  ) => {
    const response = await client.get("/analytics/export", {
      params: { report_type: reportType, export_format: format },
      responseType: "blob",
    })
    return response.data as Blob
  },
}

export const auditAPI = {
  list: async (params: { skip?: number; limit?: number } = {}) => {
    const response = await client.get("/audit/logs", { params })
    return response.data as AuditLogListResponse
  },
}

// RAG API
export const ragAPI = {
  uploadDocument: async (file: File, documentType = "onboarding_policy") => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("document_type", documentType)

    const response = await client.post("/rag/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    })
    return response.data as RagDocument
  },

  chat: async (data: RagChatRequest) => {
    const response = await client.post("/rag/chat", data)
    return response.data as RagChatResponse
  },

  search: async (query: string, top_k = 5) => {
    const response = await client.post("/rag/search", { query, top_k })
    return response.data as Array<{
      content: string
      score: number
      document_id: string | null
      document_name: string | null
      document_type: string | null
      chunk_index: number | null
      file_path: string | null
    }>
  },

  listDocuments: async () => {
    const response = await client.get("/rag/documents")
    return response.data as RagDocument[]
  },

  deleteDocument: async (documentId: string) => {
    const response = await client.delete(`/rag/documents/${documentId}`)
    return response.data as { success: boolean; document_id: string }
  },
}

// Notification API
export const notificationsAPI = {
  list: async (params: { skip?: number; limit?: number; unread_only?: boolean } = {}) => {
    const response = await client.get("/notifications", { params })
    return response.data as NotificationListResponse
  },

  unreadCount: async () => {
    const response = await client.get("/notifications/unread-count")
    return response.data as NotificationUnreadCountResponse
  },

  markRead: async (notificationId: string) => {
    const response = await client.patch(`/notifications/${notificationId}/read`)
    return response.data as NotificationItem
  },

  markAllRead: async () => {
    const response = await client.patch("/notifications/read-all")
    return response.data as { updated: number }
  },
}

export default client
