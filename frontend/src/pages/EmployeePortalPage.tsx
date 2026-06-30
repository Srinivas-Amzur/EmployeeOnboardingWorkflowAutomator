import React, { useMemo } from "react"
import { Link } from "react-router-dom"
import { CalendarClock, CheckCircle2, FileText, ListTodo, UserRound, Sparkles, Bell } from "lucide-react"
import { Card } from "../components/common/Card"
import { EmptyState } from "../components/common/EmptyState"
import { ProgressBar } from "../components/common/ProgressBar"
import { Skeleton, SkeletonText } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import { Button } from "../components/common/Button"
import { useCurrentUser, useMeetings, useMyEmployee, useNotifications, useRagDocuments, useWorkflowTasks, useWorkflows } from "../hooks"
import { formatRelativeTime } from "../lib/time"

const STAGES = [
  "initiated",
  "hr_review",
  "provisioning",
  "meetings_scheduled",
  "documents_shared",
  "completed",
]

const STAGE_LABELS: Record<string, string> = {
  initiated: "Initiated",
  hr_review: "HR Review",
  provisioning: "Provisioning",
  meetings_scheduled: "Meetings Scheduled",
  documents_shared: "Documents Shared",
  completed: "Completed",
}

const STAGE_OWNERS: Record<string, string> = {
  initiated: "HR Operations",
  hr_review: "HR Team",
  provisioning: "IT Support",
  meetings_scheduled: "People Operations",
  documents_shared: "HR Compliance",
  completed: "Onboarding PMO",
}

export const EmployeePortalPage: React.FC = () => {
  const { data: user } = useCurrentUser()
  const { data: myEmployee, isLoading: employeeLoading, error: employeeError } = useMyEmployee()
  const { data: documents = [], isLoading: docsLoading } = useRagDocuments()
  const { data: notifications } = useNotifications({ limit: 12 })
  const WORKFLOW_QUERY_LIMIT = 20

  const canQueryWorkflows = !!myEmployee
  const employeeProfileUnavailable = !employeeLoading && (!!employeeError || (!!user && !myEmployee))

  const { data: workflows = [], isLoading: workflowsLoading } = useWorkflows({
    employee_id: myEmployee?.id,
    limit: WORKFLOW_QUERY_LIMIT,
    enabled: canQueryWorkflows,
  })

  const activeWorkflow = useMemo(() => {
    return workflows.find((wf) => wf.current_state !== "completed") ?? workflows[0] ?? null
  }, [workflows])

  const { data: tasks = [], isLoading: tasksLoading } = useWorkflowTasks(activeWorkflow?.id ?? null)
  const { data: employeeMeetings = [], isLoading: meetingsLoading } = useMeetings({
    employee_id: myEmployee?.id,
    upcoming_only: true,
    limit: 8,
    enabled: !!myEmployee,
  })

  const taskSummary = useMemo(() => {
    const total = tasks.length
    const completed = tasks.filter((task) => task.status === "completed").length
    const pending = tasks.filter((task) => task.status === "pending").length
    const inProgress = tasks.filter((task) => task.status === "in_progress").length
    return { total, completed, pending, inProgress }
  }, [tasks])

  const currentStageIndex = STAGES.indexOf(activeWorkflow?.current_state ?? "initiated")

  const timelineItems = useMemo(() => {
    const notificationEvents = (notifications?.items ?? []).slice(0, 6).map((item) => ({
      id: item.id,
      title: item.title,
      message: item.message,
      when: item.created_at,
      type: "notification" as const,
    }))

    const meetingEvents = employeeMeetings.slice(0, 3).map((meeting) => ({
      id: meeting.id,
      title: meeting.title,
      message: `Meeting ${meeting.status}`,
      when: meeting.scheduled_for,
      type: "meeting" as const,
    }))

    return [...notificationEvents, ...meetingEvents]
      .sort((a, b) => new Date(b.when).getTime() - new Date(a.when).getTime())
      .slice(0, 10)
  }, [employeeMeetings, notifications?.items])

  const firstName = myEmployee
    ? myEmployee.first_name
    : (user?.name?.split(" ")[0] ?? "there")

  const completion = Math.round(activeWorkflow?.completion_percentage ?? 0)
  const joiningDate = myEmployee?.joining_date
    ? new Date(myEmployee.joining_date)
    : null
  const dayNumber = joiningDate
    ? Math.max(1, Math.ceil((Date.now() - joiningDate.getTime()) / 86400000))
    : null

  return (
    <section className="space-y-4">
      {/* â”€â”€ Welcome banner â”€â”€ */}
      <div className="relative overflow-hidden rounded-xl border border-violet-200 bg-gradient-to-br from-blue-600 to-blue-700 p-5 text-white dark:border-violet-500/20 dark:from-blue-700 dark:to-blue-800">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium text-violet-200">Employee Self-Service Portal</p>
            <h1 className="mt-1 text-2xl font-semibold">
              Welcome back, {firstName}
              {dayNumber && <span className="ml-2 text-base font-normal text-violet-300">&middot; Day {dayNumber}</span>}
            </h1>
            {myEmployee && (
              <p className="mt-1 text-sm text-violet-200">
                {myEmployee.department} &middot; {myEmployee.designation}
              </p>
            )}
          </div>
          <div className="flex flex-shrink-0 items-center gap-2">
            <Link to="/assistant">
              <Button size="sm" variant="outline" className="border-white/30 text-white hover:bg-white/10">
                <Sparkles className="h-3.5 w-3.5" />
                AI Assistant
              </Button>
            </Link>
          </div>
        </div>

        {/* Progress bar */}
        {activeWorkflow && (
          <div className="mt-4">
            <div className="mb-1.5 flex items-center justify-between">
              <p className="text-xs font-medium text-violet-200">Onboarding Progress</p>
              <p className="text-xs font-semibold tabular-nums text-white">{completion}%</p>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-white/20">
              <div
                className="h-full rounded-full bg-white transition-all duration-500"
                style={{ width: `${completion}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* â”€â”€ KPI row â”€â”€ */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          { label: "My Tasks", value: tasksLoading ? "-" : taskSummary.total, icon: ListTodo, tone: "text-blue-600 dark:text-violet-400", bg: "bg-violet-50 dark:bg-violet-500/10" },
          { label: "Documents", value: docsLoading ? "-" : documents.length, icon: FileText, tone: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-500/10" },
          { label: "Meetings", value: meetingsLoading ? "-" : employeeMeetings.length, icon: CalendarClock, tone: "text-violet-600 dark:text-violet-400", bg: "bg-violet-50 dark:bg-violet-500/10" },
          { label: "Notifications", value: notifications?.items.length ?? 0, icon: Bell, tone: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-500/10" },
        ].map((k) => {
          const Icon = k.icon
          return (
            <div key={k.label} className="kpi-card">
              <div className="flex items-start justify-between">
                <p className="section-label">{k.label}</p>
                <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${k.bg}`}>
                  <Icon className={`h-4 w-4 ${k.tone}`} />
                </span>
              </div>
              <p className="mt-2 text-3xl font-bold tabular-nums tracking-tight text-slate-900 dark:text-slate-100">{k.value}</p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Upcoming meetings</p>
          {meetingsLoading ? <Skeleton className="mt-3 h-10 w-24" /> : <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{employeeMeetings.length}</p>}
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Orientation and team sessions scheduled for your onboarding.</p>
        </Card>

        <Card className="md:col-span-1 xl:col-span-2">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Today at a glance</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-xs text-slate-500 dark:text-slate-400">Pending</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{taskSummary.pending}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-xs text-slate-500 dark:text-slate-400">In progress</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{taskSummary.inProgress}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-xs text-slate-500 dark:text-slate-400">Completed</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{taskSummary.completed}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Employee Progress Tracker">
        {!activeWorkflow && (employeeLoading || workflowsLoading) && (
          <div className="space-y-2">
            <SkeletonText className="h-4 w-1/3" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}

        {employeeProfileUnavailable && !activeWorkflow && (
          <EmptyState
            title="Employee profile not found"
            description="Your employee profile is not linked yet. Contact HR to complete profile linkage and workflow assignment."
          />
        )}

        {!activeWorkflow && !employeeLoading && !workflowsLoading && !employeeProfileUnavailable && (
          <EmptyState
            title="No active onboarding workflow"
            description="A workflow will appear here once onboarding is initiated for your profile."
          />
        )}

        {activeWorkflow && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Current Stage</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">{STAGE_LABELS[activeWorkflow.current_state] ?? activeWorkflow.current_state}</p>
                <p className="mt-1 text-xs text-slate-500">Owner: {STAGE_OWNERS[activeWorkflow.current_state] ?? "Operations"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Employee</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">{myEmployee ? `${myEmployee.first_name} ${myEmployee.last_name}` : user?.name ?? "-"}</p>
                <p className="mt-1 text-xs text-slate-500">{user?.email}</p>
                {myEmployee?.company_email && (
                  <p className="mt-0.5 text-xs font-medium text-violet-600 dark:text-violet-400">{myEmployee.company_email}</p>
                )}
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Workflow</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">#{activeWorkflow.id.substring(0, 8)}</p>
                <p className="mt-1 text-xs text-slate-500">Started {formatRelativeTime(activeWorkflow.started_at)}</p>
              </div>
            </div>

            <ProgressBar value={activeWorkflow.completion_percentage} label="Overall Progress" />

            {/* Horizontal stepper */}
            <div className="overflow-x-auto pb-1">
              <div className="flex min-w-max items-center gap-0">
                {STAGES.map((stage, index) => {
                  const isComplete = index < currentStageIndex
                  const isCurrent = index === currentStageIndex
                  const isLast = index === STAGES.length - 1
                  return (
                    <React.Fragment key={stage}>
                      <div className="flex flex-col items-center gap-1.5">
                        <div className={[
                          "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-colors",
                          isComplete ? "bg-emerald-500 text-white" :
                          isCurrent  ? "bg-violet-600 text-white" :
                          "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400",
                        ].join(" ")}>
                          {isComplete ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
                        </div>
                        <span className={[
                          "max-w-[72px] text-center text-xs font-medium leading-tight",
                          isCurrent ? "text-blue-600 dark:text-violet-400" :
                          isComplete ? "text-emerald-600 dark:text-emerald-400" :
                          "text-slate-400 dark:text-slate-500",
                        ].join(" ")}>
                          {STAGE_LABELS[stage]}
                        </span>
                      </div>
                      {!isLast && (
                        <div className={[
                          "mx-1 mb-5 h-0.5 w-12 flex-shrink-0",
                          isComplete ? "bg-emerald-400" : "bg-slate-200 dark:bg-slate-700",
                        ].join(" ")} />
                      )}
                    </React.Fragment>
                  )
                })}
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <Link to="/notifications">
                <Button variant="outline" size="sm">View notifications</Button>
              </Link>
            </div>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card title="My Tasks">
          {tasksLoading && (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}

          {!tasksLoading && tasks.length === 0 && (
            <EmptyState title="No tasks yet" description="Assigned onboarding tasks will appear here as your workflow progresses." />
          )}

          {!tasksLoading && tasks.length > 0 && (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Assignee</th>
                    <th>Due</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.slice(0, 8).map((task) => (
                    <tr key={task.id}>
                      <td className="font-medium text-slate-800 dark:text-slate-200">{task.title}</td>
                      <td className="text-xs text-slate-500 dark:text-slate-400">
                        <span className="inline-flex items-center gap-1">
                          <UserRound className="h-3.5 w-3.5" />
                          {task.assigned_to ? task.assigned_to.substring(0, 8) : "Unassigned"}
                        </span>
                      </td>
                      <td className="text-xs text-slate-500 dark:text-slate-400">{task.due_date ? new Date(task.due_date).toLocaleDateString() : "-"}</td>
                      <td><StatusBadge value={task.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <Link to="/notifications">
              <Button variant="outline" size="sm">View all updates</Button>
            </Link>
          </div>
        </Card>

        <Card title="My Timeline">
          {timelineItems.length === 0 ? (
            <EmptyState title="No activity timeline" description="Workflow updates and meeting events appear here." />
          ) : (
            <div className="space-y-0">
              {timelineItems.map((item, index) => (
                <div key={item.id} className="flex gap-3 py-2.5">
                  <div className="flex flex-col items-center">
                    <span className={`timeline-dot ${item.type === "meeting" ? "bg-violet-500" : "bg-amber-500"}`} />
                    {index < timelineItems.length - 1 && <div className="mt-1 h-full w-px bg-slate-200 dark:bg-slate-700" />}
                  </div>
                  <div className="min-w-0 flex-1 pb-2">
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{item.title}</p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{item.message}</p>
                    <p className="mt-1 text-xs text-slate-400">{formatRelativeTime(item.when)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <Link to="/notifications">
              <Button variant="outline" size="sm">Open notifications center</Button>
            </Link>
          </div>
        </Card>
      </div>

      <Card title="My Documents">
        {docsLoading && (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}

        {!docsLoading && documents.length === 0 && (
          <EmptyState title="No uploaded documents" description="Indexed onboarding documents will appear here." />
        )}

        {!docsLoading && documents.length > 0 && (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Chunks</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.document_id}>
                    <td className="font-medium text-slate-800 dark:text-slate-200">
                      <span className="inline-flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5 text-slate-500" />
                        {document.document_name}
                      </span>
                    </td>
                    <td className="text-xs text-slate-500 dark:text-slate-400">{document.document_type}</td>
                    <td className="text-xs text-slate-500 dark:text-slate-400">{document.chunks_indexed ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card title="My Meetings">
        {meetingsLoading && (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}

        {!meetingsLoading && employeeMeetings.length === 0 && (
          <EmptyState
            title="No meetings scheduled"
            description="Orientation, manager introduction, and team onboarding sessions will show up here."
          />
        )}

        {!meetingsLoading && employeeMeetings.length > 0 && (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Meeting</th>
                  <th>Schedule</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {employeeMeetings.map((meeting) => (
                  <tr key={meeting.id}>
                    <td className="font-medium text-slate-800 dark:text-slate-200">
                      <span className="inline-flex items-center gap-1.5">
                        <CalendarClock className="h-3.5 w-3.5 text-slate-500" />
                        {meeting.title}
                      </span>
                    </td>
                    <td className="text-xs text-slate-500 dark:text-slate-400">{new Date(meeting.scheduled_for).toLocaleString()}</td>
                    <td className="text-xs text-slate-500 dark:text-slate-400">{meeting.duration_minutes} min</td>
                    <td><StatusBadge value={meeting.status} /></td>
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
