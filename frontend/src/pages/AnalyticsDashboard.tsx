import React, { useMemo } from "react"
import { Download, FileText, Timer, TrendingUp, Users, AlertTriangle, CheckCircle2 } from "lucide-react"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { EmptyState } from "../components/common/EmptyState"
import { ProgressBar } from "../components/common/ProgressBar"
import { Skeleton } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import { CountUpNumber } from "../components/common/CountUpNumber"
import { useDashboardStats, useEmployees, useWorkflows } from "../hooks"
import { analyticsAPI } from "../lib/api"

const CHART_COLORS = ["#2563eb", "#14b8a6", "#f59e0b", "#8b5cf6", "#22c55e", "#ef4444"]

export const AnalyticsDashboard: React.FC = () => {
  const { data: stats, isLoading } = useDashboardStats()
  const { data: workflows = [] } = useWorkflows({ skip: 0, limit: 30 })
  const { data: employees = [] } = useEmployees(0, 500)

  const downloadReport = async (reportType: "workflow" | "employee" | "audit", format: "csv" | "pdf") => {
    const blob = await analyticsAPI.exportReport(reportType, format)
    const url = globalThis.URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = `${reportType}_report.${format}`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    globalThis.URL.revokeObjectURL(url)
  }

  const stateData = useMemo(() => {
    if (!stats?.workflows_by_state) return []
    return Object.entries(stats.workflows_by_state).map(([state, count], index) => ({
      state,
      count: Number(count),
      fill: CHART_COLORS[index % CHART_COLORS.length],
    }))
  }, [stats?.workflows_by_state])

  const taskData = useMemo(() => {
    if (!stats) return []
    return [
      { status: "completed", total: stats.completed_tasks },
      { status: "in_progress", total: stats.in_progress_tasks },
      { status: "pending", total: stats.pending_tasks },
    ]
  }, [stats])

  const trendData = useMemo(() => {
    return [...workflows]
      .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime())
      .slice(-10)
      .map((workflow) => ({
        date: new Date(workflow.started_at).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        completion: workflow.completion_percentage,
      }))
  }, [workflows])

  const departmentAnalytics = useMemo(() => {
    const employeeDepartment = new Map(employees.map((employee) => [employee.id, employee.department]))
    const grouped = new Map<string, { total: number; completionTotal: number; delayed: number }>()

    for (const workflow of workflows) {
      const department = employeeDepartment.get(workflow.employee_id) ?? "Unassigned"
      const current = grouped.get(department) ?? { total: 0, completionTotal: 0, delayed: 0 }
      current.total += 1
      current.completionTotal += workflow.completion_percentage
      if (workflow.current_state !== "completed" && workflow.completion_percentage < 40) {
        current.delayed += 1
      }
      grouped.set(department, current)
    }

    return Array.from(grouped.entries())
      .map(([department, values]) => ({
        department,
        workflows: values.total,
        avgCompletion: values.total > 0 ? Math.round(values.completionTotal / values.total) : 0,
        delayed: values.delayed,
      }))
      .sort((a, b) => b.workflows - a.workflows)
      .slice(0, 6)
  }, [employees, workflows])

  const bottlenecks = useMemo(() => {
    if (!stats?.workflows_by_state) return []
    return Object.entries(stats.workflows_by_state)
      .filter(([state]) => state !== "completed")
      .map(([state, count]) => ({ state, count: Number(count) }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
  }, [stats?.workflows_by_state])

  if (isLoading) {
    return (
      <section className="space-y-4">
        <Skeleton className="h-10 w-72 rounded-xl" />
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {["an-1","an-2","an-3","an-4"].map((key) => (
            <Skeleton key={key} className="h-20 rounded-xl" />
          ))}
        </div>
      </section>
    )
  }

  if (!stats) {
    return <EmptyState title="No analytics data" description="Analytics will appear as workflows and tasks are processed." />
  }

  const totalTasks = stats.completed_tasks + stats.pending_tasks + stats.in_progress_tasks
  const completedRate = totalTasks > 0 ? (stats.completed_tasks / totalTasks) * 100 : 0
  const inProgressRate = totalTasks > 0 ? (stats.in_progress_tasks / totalTasks) * 100 : 0
  const pendingRate = totalTasks > 0 ? (stats.pending_tasks / totalTasks) * 100 : 0

  const kpis = [
    {
      title: "Total workflows",
      value: stats.total_workflows,
      hint: `${stats.active_workflows} active · ${stats.completed_workflows} completed`,
      icon: Users,
      tone: "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-200",
    },
    {
      title: "Average completion",
      value: stats.average_completion,
      hint: "Live completion rate across all tracked workflows",
      icon: TrendingUp,
      tone: "bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-200",
      suffix: "%",
    },
    {
      title: "Delayed workflows",
      value: stats.delayed_workflows ?? 0,
      hint: "Escalated workflows needing management attention",
      icon: AlertTriangle,
      tone: "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-200",
    },
    {
      title: "Documents uploaded",
      value: stats.documents_uploaded ?? 0,
      hint: "Indexed onboarding documents and references",
      icon: FileText,
      tone: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-200",
    },
    {
      title: "Task completion",
      value: Math.round(completedRate),
      hint: "Completed tasks as a percentage of total tasks",
      icon: CheckCircle2,
      tone: "bg-slate-100 text-slate-700 dark:bg-slate-700/40 dark:text-slate-200",
      suffix: "%",
    },
  ]

  return (
    <section className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Onboarding Analytics</h1>
          <p className="page-subtitle">Operational visibility across workflows, tasks, and readiness.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {([
            { label: "Workflows", type: "workflow" as const },
            { label: "Employees", type: "employee" as const },
            { label: "Audit", type: "audit" as const },
          ]).map((r) => (
            <div key={r.type} className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{r.label}:</span>
              <button
                onClick={() => downloadReport(r.type, "csv")}
                className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                style={{ borderColor: "var(--surface-border)" }}
              >
                <Download className="h-3.5 w-3.5" />CSV
              </button>
              <button
                onClick={() => downloadReport(r.type, "pdf")}
                className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                style={{ borderColor: "var(--surface-border)" }}
              >
                <Download className="h-3.5 w-3.5" />PDF
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {kpis.map((kpi) => {
          const Icon = kpi.icon
          return (
            <div key={kpi.title} className="kpi-card">
              <div className="flex items-start justify-between">
                <p className="section-label">{kpi.title}</p>
                <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${kpi.tone}`}><Icon className="h-4 w-4" /></span>
              </div>
              <div className="mt-2 flex items-baseline gap-1">
                <CountUpNumber value={kpi.value} className="text-3xl font-bold tabular-nums tracking-tight text-slate-900 dark:text-slate-100" />
                {kpi.suffix && <span className="ml-0.5 text-xl font-semibold text-slate-400">{kpi.suffix}</span>}
              </div>
              <p className="mt-1 text-xs text-slate-400 dark:text-slate-500 line-clamp-1">{kpi.hint}</p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="section-shell">
          <p className="section-label mb-3">Workflow States</p>
          {stateData.length === 0 ? (
            <EmptyState title="No state data" description="Workflows by state will appear here." />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={stateData} dataKey="count" nameKey="state" innerRadius={36} outerRadius={68} paddingAngle={2}>
                    {stateData.map((entry, index) => (
                      <Cell key={entry.state} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5">
            {stateData.map((entry) => (
              <StatusBadge key={entry.state} value={entry.state} />
            ))}
          </div>
        </div>

        <div className="section-shell">
          <p className="section-label mb-3">Task Status</p>
          <div className="space-y-2.5">
            <ProgressBar value={completedRate} label={`Completed (${stats.completed_tasks})`} tone="success" />
            <ProgressBar value={inProgressRate} label={`In Progress (${stats.in_progress_tasks})`} tone="primary" />
            <ProgressBar value={pendingRate} label={`Pending (${stats.pending_tasks})`} tone="warning" />
          </div>
          <div className="mt-3 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={taskData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f020" />
                <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="section-shell">
          <p className="section-label mb-3">Completion Trend</p>
          {trendData.length === 0 ? (
            <EmptyState title="No trend data" description="Completion trend appears as workflows accumulate." />
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f020" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                  <Area type="monotone" dataKey="completion" stroke="#0ea5e9" fill="#bae6fd50" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="section-shell">
          <p className="section-label mb-3">Task Completion Health</p>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/70">
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Execution snapshot</p>
                <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">Completed tasks outpace WIP when onboarding is healthy.</p>
              </div>
              <StatusBadge value={stats.delayed_workflows > 0 ? "warning" : "success"} />
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "Completed", value: stats.completed_tasks, cls: "" },
                { label: "In Progress", value: stats.in_progress_tasks, cls: "" },
                { label: "Pending", value: stats.pending_tasks, cls: "" },
              ].map((t) => (
                <div key={t.label} className={`rounded-xl border border-slate-200 bg-white/80 px-3 py-2.5 text-center dark:border-slate-700 dark:bg-slate-950/40 ${t.cls}`}>
                  <p className="text-xl font-bold tabular-nums text-slate-900 dark:text-slate-100">{t.value}</p>
                  <p className="section-label mt-0.5">{t.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="section-shell">
          <p className="section-label mb-3">Key Insights</p>
          <div className="space-y-2">
            {[
              stats.delayed_workflows > 0
                ? { icon: AlertTriangle, color: "text-rose-600 dark:text-rose-400", bg: "bg-rose-50 dark:bg-rose-500/10", title: `${stats.delayed_workflows} delayed workflow${stats.delayed_workflows > 1 ? "s" : ""}`, desc: "These workflows are behind expected progress. Consider escalating." }
                : { icon: CheckCircle2, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-500/10", title: "All workflows on track", desc: "No workflows are currently flagged as delayed." },
              stats.pending_tasks > stats.completed_tasks
                ? { icon: Timer, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-500/10", title: "Pending tasks exceed completed", desc: `${stats.pending_tasks} pending vs ${stats.completed_tasks} completed. Review task assignments.` }
                : { icon: TrendingUp, color: "text-blue-600 dark:text-violet-400", bg: "bg-violet-50 dark:bg-violet-500/10", title: "Task completion is healthy", desc: `${stats.completed_tasks} tasks completed â€” workflow velocity is good.` },
              { icon: FileText, color: "text-violet-600 dark:text-violet-400", bg: "bg-violet-50 dark:bg-violet-500/10", title: "Completion rate", desc: `Average onboarding completion is ${Math.round(stats.average_completion)}%. Industry target: 80%.` },
            ].map((item) => (
              <div key={item.title} className={`flex items-start gap-3 rounded-lg border-0 px-3 py-2.5 ${item.bg}`}>
                <item.icon className={`mt-0.5 h-4 w-4 flex-shrink-0 ${item.color}`} />
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</p>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="section-shell">
          <p className="section-label mb-3">Department Analytics</p>
          {departmentAnalytics.length === 0 ? (
            <EmptyState title="No department analytics" description="Department metrics appear once employee-workflow associations are available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Department</th>
                    <th>Workflows</th>
                    <th>Avg Completion</th>
                    <th>Delayed</th>
                  </tr>
                </thead>
                <tbody>
                  {departmentAnalytics.map((row) => (
                    <tr key={row.department}>
                      <td className="font-medium text-slate-800 dark:text-slate-200">{row.department}</td>
                      <td className="text-slate-600 dark:text-slate-300">{row.workflows}</td>
                      <td className="text-slate-600 dark:text-slate-300">{row.avgCompletion}%</td>
                      <td>
                        <StatusBadge value={row.delayed > 0 ? "warning" : "success"} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="section-shell">
          <p className="section-label mb-3">Workflow Bottlenecks</p>
          {bottlenecks.length === 0 ? (
            <EmptyState title="No bottleneck states" description="Bottleneck analysis appears when state distribution is available." />
          ) : (
            <div className="space-y-2">
              {bottlenecks.map((row) => (
                <div key={row.state} className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold capitalize text-slate-900 dark:text-slate-100">{row.state.replaceAll("_", " ")}</p>
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{row.count}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                    <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(100, (row.count / Math.max(1, stats.total_workflows)) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}