import React, { useMemo } from "react"
import { Link, useNavigate } from "react-router-dom"
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  CalendarDays,
  CheckCircle2,
  Clock,
  Plus,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts"
import { Button } from "../components/common/Button"
import { CountUpNumber } from "../components/common/CountUpNumber"
import { EmptyState } from "../components/common/EmptyState"
import { ProgressBar } from "../components/common/ProgressBar"
import { Skeleton } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import { useDashboardStats, useMeetings, useNotifications, useWorkflows } from "../hooks"
import { useAuthStore } from "../store"
import { getNotificationIcon, getNotificationSeverity } from "../lib/notifications"
import { formatRelativeTime } from "../lib/time"

// â”€â”€ Constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const STAGE_COLORS: Record<string, string> = {
  initiated:          "#7c3aed",
  hr_review:          "#d97706",
  provisioning:       "#2563eb",
  meetings_scheduled: "#0891b2",
  documents_shared:   "#059669",
  completed:          "#16a34a",
}

const STATE_LABELS: Record<string, string> = {
  initiated:          "Initiated",
  hr_review:          "HR Review",
  provisioning:       "Provisioning",
  meetings_scheduled: "Meetings",
  documents_shared:   "Docs Shared",
  completed:          "Completed",
}

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return "Good morning"
  if (h < 17) return "Good afternoon"
  return "Good evening"
}

// â”€â”€ Custom tooltip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const CustomBarTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) => {
  if (!active || !payload?.[0]) return null
  return (
    <div className="rounded-lg border px-3 py-2 text-sm shadow-elevation-2"
      style={{ borderColor: "var(--surface-border)", backgroundColor: "var(--surface-base)" }}>
      <p className="font-semibold text-slate-900 dark:text-slate-100">{label}</p>
      <p className="text-slate-500 dark:text-slate-400">{payload[0].value} workflows</p>
    </div>
  )
}

// â”€â”€ Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const DashboardPage: React.FC = () => {
  const navigate  = useNavigate()
  const user      = useAuthStore((s) => s.user)

  const { data: stats,            isLoading: statsLoading }     = useDashboardStats()
  const { data: recentWorkflows = [], isLoading: workflowsLoading } = useWorkflows({ skip: 0, limit: 20 })
  const { data: activityFeed }                                   = useNotifications({ limit: 8, refetchInterval: 30_000 })
  const { data: upcomingMeetings = [], isLoading: meetingsLoading } = useMeetings({ upcoming_only: true, limit: 5 })

  // Workflow pipeline bar-chart data
  const pipelineData = useMemo(() => {
    if (!stats?.workflows_by_state) return []
    return Object.entries(stats.workflows_by_state).map(([state, count]) => ({
      label: STATE_LABELS[state] ?? state,
      count: Number(count),
      state,
      fill:  STAGE_COLORS[state] ?? "#64748b",
    }))
  }, [stats?.workflows_by_state])

  // Task stats
  const done    = stats?.completed_tasks ?? 0
  const active  = stats?.in_progress_tasks ?? 0
  const pending = stats?.pending_tasks ?? 0
  const total   = done + active + pending
  const completionRatio = total > 0 ? (done / total) * 100 : 0

  // Activity items
  const recentActivity = (stats?.recent_activity as Array<{ id: string; type: string; title: string; message: string; timestamp: string }> | undefined) ?? []
  const activityItems  = recentActivity.length > 0
    ? recentActivity.map((item) => ({ ...item, created_at: item.timestamp, notification_type: item.type }))
    : (activityFeed?.items ?? [])

  // AI insights derived from live data (no extra API call)
  const insights = useMemo(() => {
    const list: string[] = []
    if ((stats?.delayed_workflows ?? 0) > 0)
      list.push(`${stats!.delayed_workflows} workflow${stats!.delayed_workflows > 1 ? "s" : ""} are delayed â€” consider escalating.`)
    if (upcomingMeetings.length === 0 && (stats?.active_workflows ?? 0) > 0)
      list.push("No meetings scheduled for active workflows. Check your calendar.")
    if (completionRatio < 50 && total > 0)
      list.push(`Task completion is at ${Math.round(completionRatio)}%. Review pending tasks.`)
    if (list.length === 0 && (stats?.active_workflows ?? 0) > 0)
      list.push("All active workflows are progressing normally.")
    return list.slice(0, 3)
  }, [stats, upcomingMeetings.length, completionRatio, total])

  // KPI definitions
  const kpis = [
    {
      label: "Employees",
      value: stats?.total_employees ?? 0,
      icon:  Users,
      bg:    "bg-violet-50 dark:bg-violet-500/10",
      tone:  "text-blue-600 dark:text-violet-400",
      sub:   "total headcount",
    },
    {
      label: "Active Workflows",
      value: stats?.active_workflows ?? 0,
      icon:  Zap,
      bg:    "bg-emerald-50 dark:bg-emerald-500/10",
      tone:  "text-emerald-600 dark:text-emerald-400",
      sub:   "in execution",
    },
    {
      label: "Completion Rate",
      value: Math.round(stats?.average_completion ?? 0),
      icon:  TrendingUp,
      bg:    "bg-violet-50 dark:bg-violet-500/10",
      tone:  "text-violet-600 dark:text-violet-400",
      suffix: "%",
      sub:   "avg. workflow progress",
    },
    {
      label: "Delayed / At Risk",
      value: stats?.delayed_workflows ?? 0,
      icon:  AlertTriangle,
      bg:    (stats?.delayed_workflows ?? 0) > 0 ? "bg-rose-50 dark:bg-rose-500/10" : "bg-slate-50 dark:bg-slate-800",
      tone:  (stats?.delayed_workflows ?? 0) > 0 ? "text-rose-600 dark:text-rose-400" : "text-slate-500",
      sub:   (stats?.delayed_workflows ?? 0) > 0 ? "requires attention" : "on track",
    },
  ]

  const firstName = user?.name?.split(" ")[0] ?? "there"

  return (
    <section className="space-y-5">

      {/* â”€â”€ Welcome header â”€â”€ */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="page-title">
            {getGreeting()}, {firstName}
          </h1>
          <p className="page-subtitle">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            {" · "}Your onboarding operations at a glance
          </p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2">
          <Link to="/employees/new">
            <Button size="sm">
              <Plus className="h-3.5 w-3.5" />
              New Employee
            </Button>
          </Link>
          <Link to="/onboarding">
            <Button size="sm" variant="outline">
              View Workflows
            </Button>
          </Link>
        </div>
      </div>

      {/* â”€â”€ KPI strip â”€â”€ */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {kpis.map((k) => {
          const Icon = k.icon
          return statsLoading ? (
            <Skeleton key={k.label} className="h-[104px] rounded-[10px]" />
          ) : (
            <div key={k.label} className="kpi-card">
              <div className="flex items-start justify-between">
                <p className="section-label">{k.label}</p>
                <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${k.bg}`}>
                  <Icon className={`h-4 w-4 ${k.tone}`} />
                </span>
              </div>
              <p className="mt-2 text-3xl font-bold tabular-nums tracking-tight text-slate-900 dark:text-slate-100">
                <CountUpNumber value={k.value} />
                {k.suffix && <span className="ml-0.5 text-xl font-semibold text-slate-500">{k.suffix}</span>}
              </p>
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{k.sub}</p>
            </div>
          )
        })}
      </div>

      {/* â”€â”€ AI Insights banner â”€â”€ */}
      {insights.length > 0 && (
        <div className="flex items-start gap-4 rounded-[10px] border border-violet-200 bg-violet-50 px-4 py-3 dark:border-violet-500/20 dark:bg-violet-500/8">
          <Bot className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600 dark:text-violet-400" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-700 dark:text-violet-300">AI Insights</p>
            <ul className="mt-1 space-y-0.5">
              {insights.map((msg, i) => (
                <li key={i} className="text-sm text-violet-800 dark:text-violet-200">&#x2726; {msg}</li>
              ))}
            </ul>
          </div>
          <Link to="/assistant" className="flex-shrink-0 text-xs font-semibold text-violet-600 hover:underline dark:text-violet-400">
            Ask AI <ArrowRight className="inline h-3 w-3" />
          </Link>
        </div>
      )}

      {/* â”€â”€ Charts row â”€â”€ */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">

        {/* Workflow pipeline bar chart */}
        <div className="section-shell col-span-1 lg:col-span-2">
          <p className="section-label mb-4">Workflow Pipeline</p>
          {statsLoading ? (
            <Skeleton className="h-48" />
          ) : pipelineData.length === 0 ? (
            <EmptyState title="No workflows yet" description="Create an employee to start the onboarding pipeline." />
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pipelineData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(226 232 240 / 0.5)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomBarTooltip />} cursor={{ fill: "rgb(226 232 240 / 0.2)" }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={52}>
                    {pipelineData.map((entry) => (
                      <Cell key={entry.state} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Task health */}
        <div className="section-shell">
          <p className="section-label mb-4">Task Health</p>
          {statsLoading ? (
            <Skeleton className="h-48" />
          ) : (
            <div className="flex h-full flex-col justify-between gap-4">
              <div className="grid grid-cols-3 divide-x divide-slate-100 text-center dark:divide-slate-800">
                {[
                  { label: "Done",    value: done,    color: "text-emerald-600 dark:text-emerald-400" },
                  { label: "Active",  value: active,  color: "text-blue-600 dark:text-violet-400" },
                  { label: "Pending", value: pending, color: "text-amber-600 dark:text-amber-400" },
                ].map((t) => (
                  <div key={t.label} className="px-2">
                    <p className={`text-2xl font-bold tabular-nums ${t.color}`}>{t.value}</p>
                    <p className="mt-0.5 section-label">{t.label}</p>
                  </div>
                ))}
              </div>

              <ProgressBar value={completionRatio} label="Completion ratio" tone="success" />

              <div className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 dark:bg-emerald-500/10">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <p className="text-xs text-emerald-700 dark:text-emerald-300">
                  {done} tasks completed out of {total}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* â”€â”€ Bottom row: Workflows table + Meetings + Activity â”€â”€ */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_320px]">

        {/* Recent workflows table */}
        <div className="section-shell overflow-hidden !p-0">
          <div className="flex items-center justify-between px-5 py-3.5">
            <p className="section-label">Recent Workflows</p>
            <Link
              to="/onboarding"
              className="flex items-center gap-1 text-xs font-semibold text-violet-600 hover:underline dark:text-violet-400"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {workflowsLoading ? (
            <div className="space-y-px px-5 pb-4">
              {["a","b","c","d","e"].map((k) => <Skeleton key={k} className="h-12 rounded-lg" />)}
            </div>
          ) : recentWorkflows.length === 0 ? (
            <div className="px-5 pb-5">
              <EmptyState
                title="No workflows"
                description="Create an employee to begin the onboarding lifecycle."
                action={<Link to="/employees/new"><Button size="sm"><Plus className="h-3.5 w-3.5" />Create Employee</Button></Link>}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="pl-5">Employee</th>
                    <th>Stage</th>
                    <th className="w-36">Progress</th>
                    <th className="pr-5">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {recentWorkflows.slice(0, 8).map((wf) => (
                    <tr
                      key={wf.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/onboarding/${wf.id}`)}
                    >
                      <td className="pl-5">
                        <div>
                          <p className="font-mono text-sm font-semibold text-slate-700 dark:text-slate-300">
                            #{wf.id.substring(0, 8)}
                          </p>
                          <p className="text-xs text-slate-400">{wf.employee_id.substring(0, 8)}</p>
                        </div>
                      </td>
                      <td><StatusBadge value={wf.current_state} /></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 flex-1 max-w-[80px] overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                            <div
                              className="h-full rounded-full bg-violet-500 transition-all"
                              style={{ width: `${Math.round(wf.completion_percentage)}%` }}
                            />
                          </div>
                          <span className="w-8 text-right text-xs tabular-nums text-slate-500">
                            {Math.round(wf.completion_percentage)}%
                          </span>
                        </div>
                      </td>
                      <td className="pr-5 text-xs text-slate-400">{formatRelativeTime(wf.started_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right column: Meetings + Activity */}
        <div className="flex flex-col gap-4">

          {/* Upcoming meetings */}
          <div className="section-shell">
            <p className="section-label mb-3">Upcoming Meetings</p>
            {meetingsLoading && <Skeleton className="h-32" />}
            {!meetingsLoading && upcomingMeetings.length === 0 && (
              <p className="text-sm text-slate-400 dark:text-slate-500">No upcoming meetings</p>
            )}
            {!meetingsLoading && upcomingMeetings.length > 0 && (
              <div className="space-y-2">
                {upcomingMeetings.slice(0, 4).map((meeting) => (
                  <div key={meeting.id} className="flex items-center gap-2.5">
                    <CalendarDays className="h-4 w-4 flex-shrink-0 text-violet-500" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-200">
                        {meeting.title}
                      </p>
                      <p className="text-xs text-slate-400">
                        {new Date(meeting.scheduled_for).toLocaleString("en-US", {
                          month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <StatusBadge value={meeting.status} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Activity feed */}
          <div className="section-shell flex-1">
            <p className="section-label mb-3">Live Activity</p>
            {activityItems.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No recent activity</p>
            ) : (
              <div className="space-y-3 overflow-y-auto scrollbar-thin" style={{ maxHeight: 240 }}>
                {activityItems.slice(0, 8).map((item) => (
                  <div key={item.id} className="flex items-start gap-2.5">
                    <span
                      className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-slate-100 text-xs dark:bg-slate-800"
                      aria-hidden="true"
                    >
                      {getNotificationIcon(item.notification_type)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {item.title}
                      </p>
                      <p className="flex items-center gap-1 text-xs text-slate-400">
                        <Clock className="h-3 w-3" />
                        {formatRelativeTime(item.created_at)}
                      </p>
                    </div>
                    <StatusBadge value={getNotificationSeverity(item.notification_type)} className="flex-shrink-0" />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
