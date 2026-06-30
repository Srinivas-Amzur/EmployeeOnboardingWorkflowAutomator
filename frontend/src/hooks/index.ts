import { useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { analyticsAPI, auditAPI, authAPI, employeeAPI, meetingAPI, notificationsAPI, onboardingAPI, ragAPI } from "../lib/api"
import type {
  ChangePasswordRequest,
  Employee,
  LoginCredentials,
  OnboardingMeeting,
  OnboardingTask,
  RagChatRequest,
  RegisterCredentials,
  ScheduleMeetingPayload,
} from "../types"

// ── Auth ────────────────────────────────────────────────────────────────────

export function useLogin() {
  return useMutation({
    mutationFn: (credentials: LoginCredentials) => authAPI.login(credentials),
  })
}

export function useGoogleLogin() {
  return useMutation({
    mutationFn: (idToken: string) => authAPI.googleLogin(idToken),
  })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["current-user"],
    queryFn: () => authAPI.me(),
    retry: false,
    staleTime: 5 * 60_000,
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => authAPI.logout(),
    onSuccess: () => {
      queryClient.clear()
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterCredentials) => authAPI.register(data),
  })
}

export function useChangePassword() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ChangePasswordRequest) => authAPI.changePassword(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["current-user"] })
    },
  })
}

// ── Employees ────────────────────────────────────────────────────────────────

export function useEmployees(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ["employees", skip, limit],
    queryFn: () => employeeAPI.list(skip, limit),
    staleTime: 60_000,
  })
}

export function useEmployee(id: string | null) {
  return useQuery({
    queryKey: ["employee", id],
    queryFn: () => employeeAPI.get(id ?? ""),
    enabled: !!id,
  })
}

export function useMyEmployee() {
  return useQuery({
    queryKey: ["employee", "me"],
    queryFn: () => employeeAPI.me(),
    retry: false,
  })
}

export function useCreateEmployee() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof employeeAPI.create>[0]) => employeeAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
    },
  })
}

export function useUpdateEmployee() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Employee> }) =>
      employeeAPI.update(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["employees"] })
      queryClient.invalidateQueries({ queryKey: ["employee", id] })
    },
  })
}

// ── Onboarding Workflows ─────────────────────────────────────────────────────

export function useWorkflows(
  params: { employee_id?: string; skip?: number; limit?: number; enabled?: boolean } = {},
) {
  const { enabled = true, ...queryParams } = params

  return useQuery({
    queryKey: ["workflows", queryParams],
    queryFn: () => onboardingAPI.listWorkflows(queryParams),
    enabled,
  })
}

export function useOnboardingWorkflow(id: string | null) {
  return useQuery({
    queryKey: ["workflow", id],
    queryFn: () => onboardingAPI.getWorkflow(id ?? ""),
    enabled: !!id,
  })
}

export function useWorkflowProgress(id: string | null) {
  return useQuery({
    queryKey: ["workflow-progress", id],
    queryFn: () => onboardingAPI.getWorkflowProgress(id ?? ""),
    enabled: !!id,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useWorkflowSnapshot(id: string | null) {
  return useQuery({
    queryKey: ["workflow-snapshot", id],
    queryFn: () => onboardingAPI.getWorkflowSnapshot(id ?? ""),
    enabled: !!id,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useWorkflowEvents(id: string | null, limit = 50) {
  return useQuery({
    queryKey: ["workflow-events", id, limit],
    queryFn: () => onboardingAPI.getWorkflowEvents(id ?? "", limit),
    enabled: !!id,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useCreateOnboardingWorkflow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { employee_id: string; current_state?: string }) =>
      onboardingAPI.createWorkflow(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
    },
  })
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof onboardingAPI.updateWorkflow>[1] }) =>
      onboardingAPI.updateWorkflow(id, data),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["workflow", id] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
    },
  })
}

export function useWorkflowAction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      workflowId,
      action,
      note,
    }: {
      workflowId: string
      action: "pause" | "resume" | "escalate" | "complete"
      note?: string
    }) => onboardingAPI.applyWorkflowAction(workflowId, action, note),
    onSuccess: (_data, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: ["workflow", workflowId] })
      queryClient.invalidateQueries({ queryKey: ["workflow-progress", workflowId] })
      queryClient.invalidateQueries({ queryKey: ["workflow-events", workflowId] })
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

// ── Onboarding Tasks ─────────────────────────────────────────────────────────

export function useWorkflowTasks(workflowId: string | null) {
  return useQuery({
    queryKey: ["workflow-tasks", workflowId],
    queryFn: () => onboardingAPI.getWorkflowTasks(workflowId ?? ""),
    enabled: !!workflowId,
  })
}

export function useAddTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      workflowId,
      data,
    }: {
      workflowId: string
      data: Partial<OnboardingTask> & { title: string }
    }) => onboardingAPI.addTask(workflowId, data),
    onSuccess: (_data, { workflowId }) => {
      queryClient.invalidateQueries({ queryKey: ["workflow-tasks", workflowId] })
      queryClient.invalidateQueries({ queryKey: ["workflow-progress", workflowId] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
    },
  })
}

export function useUpdateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: Partial<OnboardingTask> }) =>
      onboardingAPI.updateTask(taskId, data),
    onSuccess: (updatedTask) => {
      queryClient.invalidateQueries({ queryKey: ["workflow-tasks", updatedTask.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflow-progress", updatedTask.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
    },
  })
}

// ── Meetings ───────────────────────────────────────────────────────────────

export function useMeetings(
  params: {
    employee_id?: string
    workflow_id?: string
    upcoming_only?: boolean
    skip?: number
    limit?: number
    enabled?: boolean
  } = {},
) {
  const { enabled = true, ...queryParams } = params
  return useQuery({
    queryKey: ["meetings", queryParams],
    queryFn: () => meetingAPI.list(queryParams),
    enabled,
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
  })
}

export function useCreateMeeting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof meetingAPI.create>[0]) => meetingAPI.create(data),
    onSuccess: (meeting) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] })
      queryClient.invalidateQueries({ queryKey: ["workflow", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflow-events", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

export function useUpdateMeeting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, data }: { meetingId: string; data: Partial<OnboardingMeeting> }) =>
      meetingAPI.update(meetingId, data),
    onSuccess: (meeting) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] })
      queryClient.invalidateQueries({ queryKey: ["workflow", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflow-events", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

export function useDeleteMeeting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (meetingId: string) => meetingAPI.remove(meetingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] })
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

export function useScheduleWorkflowMeeting() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      workflowId,
      kind,
      payload,
    }: {
      workflowId: string
      kind: "orientation" | "manager_introduction" | "team_onboarding"
      payload?: ScheduleMeetingPayload
    }) => {
      if (kind === "orientation") {
        return meetingAPI.scheduleOrientation(workflowId, payload)
      }
      if (kind === "manager_introduction") {
        return meetingAPI.scheduleManagerIntroduction(workflowId, payload)
      }
      return meetingAPI.scheduleTeamOnboardingSession(workflowId, payload)
    },
    onSuccess: (meeting) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] })
      queryClient.invalidateQueries({ queryKey: ["workflow", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflow-events", meeting.workflow_id] })
      queryClient.invalidateQueries({ queryKey: ["workflows"] })
      queryClient.invalidateQueries({ queryKey: ["analytics-dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

// ── Analytics ────────────────────────────────────────────────────────────────

export function useDashboardStats() {
  return useQuery({
    queryKey: ["analytics-dashboard"],
    queryFn: analyticsAPI.getDashboardStats,
    staleTime: 2 * 60_000,
    refetchInterval: 90_000,
    refetchOnWindowFocus: false,
  })
}

export function useAuditLogs(params: { skip?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ["audit-logs", params],
    queryFn: () => auditAPI.list(params),
    staleTime: 60_000,
    refetchInterval: 120_000,
    refetchOnWindowFocus: false,
  })
}

// ── RAG Assistant ───────────────────────────────────────────────────────────

export function useRagDocuments() {
  return useQuery({
    queryKey: ["rag-documents"],
    queryFn: ragAPI.listDocuments,
  })
}

export function useUploadRagDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType?: string }) =>
      ragAPI.uploadDocument(file, documentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] })
    },
  })
}

export function useDeleteRagDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId: string) => ragAPI.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] })
    },
  })
}

export function useRagChat() {
  return useMutation({
    mutationFn: (request: RagChatRequest) => ragAPI.chat(request),
  })
}

// ── Notifications ───────────────────────────────────────────────────────────

export function useNotifications(
  params: {
    skip?: number
    limit?: number
    unread_only?: boolean
    enabled?: boolean
    refetchInterval?: number
  } = {},
) {
  const {
    enabled = true,
    refetchInterval = 20_000,
    ...queryParams
  } = params

  return useQuery({
    queryKey: ["notifications", queryParams],
    queryFn: () => notificationsAPI.list(queryParams),
    enabled,
    refetchInterval,
    refetchOnWindowFocus: false,
  })
}

export function useUnreadNotificationCount(refetchInterval = 30_000) {
  return useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: notificationsAPI.unreadCount,
    staleTime: 20_000,
    refetchInterval,
    refetchOnWindowFocus: false,
  })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (notificationId: string) => notificationsAPI.markRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => notificationsAPI.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] })
      queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] })
    },
  })
}

export function useNotificationStream(enabled = true) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!enabled) return

    const wsBase = import.meta.env.VITE_WS_URL as string | undefined
    if (!wsBase) return

    let socket: WebSocket | null = null
    try {
      socket = new WebSocket(`${wsBase.replace(/\/$/, "")}/notifications`)
      socket.onmessage = () => {
        queryClient.invalidateQueries({ queryKey: ["notifications"] })
        queryClient.invalidateQueries({ queryKey: ["notifications-unread-count"] })
      }
    } catch {
      socket = null
    }

    return () => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.close()
      }
    }
  }, [enabled, queryClient])
}
