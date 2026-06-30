import React, { useEffect, useMemo, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import {
  AlertTriangle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Circle,
  Clock3,
  PauseCircle,
  PlayCircle,
  ShieldAlert,
  Sparkles,
} from "lucide-react"
import { Button } from "../components/common/Button"
import { Card } from "../components/common/Card"
import { EmptyState } from "../components/common/EmptyState"
import { ProgressBar } from "../components/common/ProgressBar"
import { Skeleton, SkeletonText } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import {
  useAddTask,
  useEmployee,
  useOnboardingWorkflow,
  useMeetings,
  useScheduleWorkflowMeeting,
  useUpdateTask,
  useWorkflowAction,
  useWorkflowEvents,
  useWorkflowTasks,
} from "../hooks"
import { formatRelativeTime } from "../lib/time"

const WORKFLOW_STAGES = ["initiated", "hr_review", "provisioning", "meetings_scheduled", "documents_shared", "completed"]

const STAGE_LABELS: Record<string, string> = {
  initiated: "Initiated",
  hr_review: "HR Review",
  provisioning: "Provisioning",
  meetings_scheduled: "Meetings Scheduled",
  documents_shared: "Documents Shared",
  completed: "Completed",
}

const STAGE_TEAMS: Record<string, string> = {
  initiated: "HR Operations",
  hr_review: "HR Team",
  provisioning: "IT Support",
  meetings_scheduled: "People Operations",
  documents_shared: "HR Compliance",
  completed: "Onboarding PMO",
}

// Tiny inline dropdown for action groups
function ActionMenu({ label, icon: Icon, items, isLoading }: {
  label: string
  icon: React.ElementType
  items: { label: string; icon: React.ElementType; onClick: () => void }[]
  isLoading?: boolean
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])
  return (
    <div className="relative" ref={ref}>
      <Button variant="secondary" size="sm" onClick={() => setOpen((v) => !v)} isLoading={isLoading}>
        <Icon className="h-3.5 w-3.5" />
        {label}
        <ChevronDown className="h-3 w-3 opacity-60" />
      </Button>
      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-1 min-w-[180px] rounded-lg border py-1 shadow-elevation-2"
          style={{ borderColor: "var(--surface-border)", backgroundColor: "var(--surface-base)" }}
        >
          {items.map((item) => {
            const ItemIcon = item.icon
            return (
              <button
                key={item.label}
                onClick={() => { item.onClick(); setOpen(false) }}
                className="flex w-full items-center gap-2.5 px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                <ItemIcon className="h-3.5 w-3.5 text-slate-400" />
                {item.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export const OnboardingDetailPage: React.FC = () => {
  const { workflowId } = useParams<{ workflowId: string }>()
  const navigate = useNavigate()

  const [showAddTask, setShowAddTask] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState("")
  const [newTaskDescription, setNewTaskDescription] = useState("")

  const { data: workflow, isLoading: workflowLoading } = useOnboardingWorkflow(workflowId ?? null)
  const { data: employee } = useEmployee(workflow?.employee_id ?? null)
  const { data: tasks = [], isLoading: tasksLoading } = useWorkflowTasks(workflowId ?? null)
  const { data: events = [] } = useWorkflowEvents(workflowId ?? null, 80)
  const { data: workflowMeetings = [], isLoading: meetingsLoading } = useMeetings({
    workflow_id: workflowId,
    limit: 20,
    enabled: !!workflowId,
  })

  const updateTask = useUpdateTask()
  const addTask = useAddTask()
  const workflowAction = useWorkflowAction()
  const scheduleMeeting = useScheduleWorkflowMeeting()

  const stageEvents = useMemo(() => {
    const map = new Map<string, string>()
    for (const event of events) {
      if (event.state_to && WORKFLOW_STAGES.includes(event.state_to) && !map.has(event.state_to)) {
        map.set(event.state_to, event.created_at)
      }
    }
    if (workflow?.started_at && !map.has("initiated")) {
      map.set("initiated", workflow.started_at)
    }
    if (workflow?.completed_at && !map.has("completed")) {
      map.set("completed", workflow.completed_at)
    }
    return map
  }, [events, workflow?.completed_at, workflow?.started_at])

  const tasksByStage = useMemo(() => {
    return WORKFLOW_STAGES.reduce<Record<string, string[]>>((acc, stage) => {
      acc[stage] = tasks
        .filter((task) => task.title.toLowerCase().includes(stage.split("_")[0]))
        .slice(0, 3)
        .map((task) => task.title)
      return acc
    }, {})
  }, [tasks])

  if (!workflowId) {
    return <p className="text-sm text-rose-700">Invalid workflow ID.</p>
  }

  if (workflowLoading) {
    return (
      <Card className="space-y-4">
        <SkeletonText className="h-6 w-1/4" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </Card>
    )
  }

  if (!workflow) {
    return (
      <EmptyState
        title="Workflow not found"
        description="This workflow may have been removed or you may not have permission to view it."
      />
    )
  }

  const currentStateIndex = WORKFLOW_STAGES.indexOf(workflow.current_state)

  const handleWorkflowAction = async (action: "pause" | "resume" | "escalate" | "complete") => {
    if (!workflowId) return
    await workflowAction.mutateAsync({ workflowId, action })
  }

  const handleScheduleMeeting = async (kind: "orientation" | "manager_introduction" | "team_onboarding") => {
    if (!workflowId) return
    await scheduleMeeting.mutateAsync({ workflowId, kind })
  }

  return (
    <section className="space-y-4">
      <header className="section-shell">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div className="space-y-2">
            <button onClick={() => navigate("/onboarding")} className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100">
              <ArrowRight className="h-4 w-4 rotate-180" />
              Back to workflows
            </button>
            <div>
              <h1 className="page-title">Workflow Detail</h1>
              <p className="page-subtitle max-w-2xl">
                A clear view of lifecycle state, task progress, activity history, and meeting readiness for this onboarding.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ActionMenu
              label="Schedule Meeting"
              icon={CalendarDays}
              isLoading={scheduleMeeting.isPending}
              items={[
                { label: "Orientation", icon: CalendarDays, onClick: () => void handleScheduleMeeting("orientation") },
                { label: "Manager Introduction", icon: CalendarDays, onClick: () => void handleScheduleMeeting("manager_introduction") },
                { label: "Team Session", icon: CalendarDays, onClick: () => void handleScheduleMeeting("team_onboarding") },
              ]}
            />
            <ActionMenu
              label="Actions"
              icon={ShieldAlert}
              isLoading={workflowAction.isPending}
              items={[
                { label: "Pause", icon: PauseCircle, onClick: () => void handleWorkflowAction("pause") },
                { label: "Resume", icon: PlayCircle, onClick: () => void handleWorkflowAction("resume") },
                { label: "Escalate", icon: ShieldAlert, onClick: () => void handleWorkflowAction("escalate") },
              ]}
            />
            <Button variant="primary" size="sm" onClick={() => void handleWorkflowAction("complete")} isLoading={workflowAction.isPending}>
              <CheckCircle2 className="h-3.5 w-3.5" />
              Complete
            </Button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 xl:grid-cols-4">
          <div className="kpi-card">
            <p className="section-label">Current state</p>
            <div className="mt-2">
              <StatusBadge value={workflow.current_state} className="text-sm" />
            </div>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Last update {formatRelativeTime(workflow.updated_at)}</p>
          </div>

          <div className="kpi-card">
            <p className="section-label">Completion</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{workflow.completion_percentage}%</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Workflow progress</p>
          </div>

          <div className="kpi-card">
            <p className="section-label">Employee</p>
            {employee ? (
              <div className="mt-2 space-y-1 text-sm">
                <p className="font-semibold text-slate-800 dark:text-slate-200">{employee.first_name} {employee.last_name}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{employee.department} &middot; {employee.designation}</p>
                {employee.company_email && (
                  <p className="text-xs font-medium text-violet-600 dark:text-violet-400">{employee.company_email}</p>
                )}
              </div>
            ) : (
              <SkeletonText className="mt-2 w-32" />
            )}
          </div>

          <div className="kpi-card">
            <p className="section-label">Meetings</p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{workflowMeetings.length}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Scheduled for this workflow</p>
          </div>
        </div>

        <div className="mt-4">
          <ProgressBar value={workflow.completion_percentage} label="Workflow Completion" />
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card title="Workflow Lifecycle" padding="sm" className="xl:col-span-1">
          <div className="space-y-3">
            {WORKFLOW_STAGES.map((stage, index) => {
              const isCompleted = index < currentStateIndex
              const isCurrent = index === currentStateIndex
              let stageToneClass = "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500"
              let stageProgressClass = "bg-transparent"
              let stageProgressWidth = "0%"
              if (isCompleted) {
                stageToneClass = "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400"
                stageProgressClass = "bg-emerald-500"
                stageProgressWidth = "100%"
              } else if (isCurrent) {
                stageToneClass = "bg-violet-100 text-blue-600 dark:bg-blue-500/20 dark:text-violet-400"
                stageProgressClass = "bg-violet-500"
                stageProgressWidth = "65%"
              }

              let stageIcon: React.ReactNode = <Circle className="h-3.5 w-3.5" />
              if (isCompleted) {
                stageIcon = <CheckCircle2 className="h-4 w-4" />
              } else if (isCurrent) {
                stageIcon = <Clock3 className="h-4 w-4" />
              }

              return (
                <div key={stage} className="rounded-xl border border-slate-200 bg-white/80 p-3 dark:border-slate-700 dark:bg-slate-950/40">
                  <div className="flex items-center gap-3">
                    <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${stageToneClass}`}>
                      {stageIcon}
                    </span>
                    <div>
                      <p className={`text-sm font-semibold ${isCurrent ? "text-slate-900 dark:text-slate-100" : "text-slate-700 dark:text-slate-300"}`}>{STAGE_LABELS[stage]}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{STAGE_TEAMS[stage]}</p>
                    </div>
                  </div>

                  {tasksByStage[stage]?.length > 0 && (
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">
                      {tasksByStage[stage].join(", ")}
                    </p>
                  )}

                  <div className="mt-2 h-1 rounded-full bg-slate-100 dark:bg-slate-700/60">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${isCompleted ? "bg-emerald-500" : stageProgressClass}`}
                      style={{ width: isCompleted ? "100%" : stageProgressWidth }}
                    />
                  </div>

                  {stageEvents.get(stage) && (
                    <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
                      {formatRelativeTime(stageEvents.get(stage) as string)}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        </Card>

        <Card title="Workflow Activity" padding="sm" className="xl:col-span-1">
          {events.length === 0 ? (
            <EmptyState title="No activity yet" description="Workflow events and escalations will appear as automation progresses." />
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Details</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {events.slice(-12).reverse().map((event) => (
                    <tr key={event.id}>
                      <td className="whitespace-nowrap font-medium capitalize text-slate-800 dark:text-slate-200">{event.event_type.replaceAll("_", " ")}</td>
                      <td className="max-w-[18rem] truncate text-slate-600 dark:text-slate-300">{event.message}</td>
                      <td>
                        <span className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
                          {event.status === "warning" ? <AlertTriangle className="h-3.5 w-3.5 text-amber-600" /> : <Sparkles className="h-3.5 w-3.5 text-violet-600" />}
                          {event.status}
                        </span>
                      </td>
                      <td className="text-xs text-slate-500 dark:text-slate-400">{formatRelativeTime(event.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card title="Workflow Meetings" padding="sm" className="xl:col-span-1">
          {meetingsLoading && (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}

          {!meetingsLoading && workflowMeetings.length === 0 && (
            <EmptyState
              title="No meetings scheduled"
              description="Use the schedule buttons above to add orientation, manager introduction, and team onboarding meetings."
            />
          )}

          {!meetingsLoading && workflowMeetings.length > 0 && (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Type</th>
                    <th>Schedule</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {workflowMeetings.map((meeting) => (
                    <tr key={meeting.id}>
                      <td className="font-medium text-slate-800 dark:text-slate-200">
                        <span className="inline-flex items-center gap-1.5">
                          <CalendarDays className="h-3.5 w-3.5 text-violet-600" />
                          {meeting.title}
                        </span>
                      </td>
                      <td className="text-slate-600 dark:text-slate-300">{meeting.meeting_type.replaceAll("_", " ")}</td>
                      <td className="text-xs text-slate-500 dark:text-slate-400">{new Date(meeting.scheduled_for).toLocaleString()}</td>
                      <td><StatusBadge value={meeting.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <Card title="Tasks" padding="none">
        <div className="mb-4 flex flex-col gap-2 border-b border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Task operations table</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Track status, priority, ownership, and due dates in one view.</p>
          </div>
          <Button onClick={() => setShowAddTask(!showAddTask)} size="sm" variant="outline">
            {showAddTask ? "Cancel" : "Add Task"}
          </Button>
        </div>

        {showAddTask && (
          <div className="mx-4 mb-4 rounded-xl border border-violet-200 bg-violet-50/80 p-3 dark:border-violet-500/20 dark:bg-violet-500/10">
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Task title"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                className="surface-input"
              />
              <textarea
                placeholder="Task description (optional)"
                value={newTaskDescription}
                onChange={(e) => setNewTaskDescription(e.target.value)}
                className="surface-input min-h-24"
                rows={3}
              />
              <Button
                onClick={() => {
                  if (!workflowId || !newTaskTitle.trim()) return
                  addTask.mutate(
                    {
                      workflowId,
                      data: {
                        title: newTaskTitle,
                        description: newTaskDescription || null,
                        status: "pending",
                        priority: "medium",
                      },
                    },
                    {
                      onSuccess: () => {
                        setShowAddTask(false)
                        setNewTaskTitle("")
                        setNewTaskDescription("")
                      },
                    },
                  )
                }}
                disabled={addTask.isPending}
                isLoading={addTask.isPending}
              >
                Create Task
              </Button>
            </div>
          </div>
        )}

        {tasksLoading && (
          <div className="space-y-2 px-4 pb-4">
            {[
              "task-1",
              "task-2",
              "task-3",
              "task-4",
            ].map((key) => (
              <div key={key} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
                <SkeletonText className="h-4 w-2/5" />
                <SkeletonText className="mt-2 h-3 w-3/5" />
                <Skeleton className="mt-3 h-8 w-32" />
              </div>
            ))}
          </div>
        )}

        {!tasksLoading && tasks.length === 0 && (
          <div className="px-4 pb-4">
            <EmptyState title="No tasks yet" description="Add your first task to progress this workflow through onboarding stages." />
          </div>
        )}

        {!tasksLoading && tasks.length > 0 && (
          <div className="overflow-x-auto pb-2">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Due Date</th>
                  <th className="w-44">Update</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <p className="font-medium text-slate-800 dark:text-slate-200">{task.title}</p>
                      {task.description && <p className="text-xs text-slate-500 dark:text-slate-400">{task.description}</p>}
                    </td>
                    <td><StatusBadge value={task.priority} /></td>
                    <td><StatusBadge value={task.status} /></td>
                    <td className="text-xs text-slate-500 dark:text-slate-400">{task.due_date ? new Date(task.due_date).toLocaleDateString() : "-"}</td>
                    <td>
                      <select
                        value={task.status}
                        onChange={(e) => {
                          updateTask.mutate({
                            taskId: task.id,
                            data: { status: e.target.value },
                          })
                        }}
                        className="surface-select text-xs font-medium"
                        aria-label={`Update status for ${task.title}`}
                      >
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="blocked">Blocked</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  )
}