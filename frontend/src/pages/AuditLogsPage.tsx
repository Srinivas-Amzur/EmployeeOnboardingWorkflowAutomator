import React, { useMemo, useState } from "react"
import { Activity, Clock3, FileSearch, Filter, RefreshCcw, ShieldCheck, BadgeCheck, AlertTriangle, CircleAlert } from "lucide-react"
import { Button } from "../components/common/Button"
import { Card } from "../components/common/Card"
import { EmptyState } from "../components/common/EmptyState"
import { Skeleton, SkeletonText } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import { useAuditLogs } from "../hooks"
import { formatRelativeTime } from "../lib/time"

const PAGE_SIZE = 120

const ACTION_TONES: Record<string, string> = {
  "Employee Created": "success",
  "Workflow Started": "info",
  "Workflow Updated": "warning",
  "Workflow Completed": "success",
  "Task Created": "info",
  "Task Updated": "warning",
  "Notification Generated": "info",
  "Document Uploaded": "success",
  "AI Query Executed": "info",
}

export const AuditLogsPage: React.FC = () => {
  const [search, setSearch] = useState("")
  const [actionFilter, setActionFilter] = useState("all")
  const [dateFilter, setDateFilter] = useState("all")
  const { data, isLoading, refetch, isFetching } = useAuditLogs({ skip: 0, limit: PAGE_SIZE })

  const items = data?.items ?? []

  const availableActions = useMemo(() => {
    return Array.from(new Set(items.map((item) => item.action))).sort((a, b) => a.localeCompare(b))
  }, [items])

  const filteredItems = useMemo(() => {
    const now = Date.now()
    return items.filter((item) => {
      const matchesAction = actionFilter === "all" || item.action === actionFilter
      const query = search.trim().toLowerCase()
      const matchesSearch =
        query.length === 0 ||
        item.user.toLowerCase().includes(query) ||
        item.action.toLowerCase().includes(query) ||
        item.entity.toLowerCase().includes(query) ||
        item.details.toLowerCase().includes(query)

      const timestamp = new Date(item.timestamp).getTime()
      const ageHours = (now - timestamp) / (1000 * 60 * 60)
      const matchesDate =
        dateFilter === "all" ||
        (dateFilter === "day" && ageHours <= 24) ||
        (dateFilter === "week" && ageHours <= 24 * 7) ||
        (dateFilter === "month" && ageHours <= 24 * 30)

      return matchesAction && matchesSearch && matchesDate
    })
  }, [actionFilter, dateFilter, items, search])

  const riskCount = filteredItems.filter((item) => ACTION_TONES[item.action] === "warning").length
  const successCount = filteredItems.filter((item) => ACTION_TONES[item.action] === "success").length
  const infoCount = filteredItems.filter((item) => ACTION_TONES[item.action] === "info").length

  const resolveActionTone = (action: string) => ACTION_TONES[action] ?? "info"

  const resolveActionIcon = (action: string) => {
    const tone = resolveActionTone(action)
    if (tone === "success") return <BadgeCheck className="h-4 w-4" />
    if (tone === "warning") return <AlertTriangle className="h-4 w-4" />
    if (tone === "error") return <CircleAlert className="h-4 w-4" />
    return <Activity className="h-4 w-4" />
  }

  return (
    <section className="space-y-4">
      <header className="sticky top-[56px] z-10 section-shell">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="page-title">Audit Logs</h1>
            <p className="page-subtitle">Operational traceability across workflows, tasks, notifications, documents, and AI activity.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()} isLoading={isFetching}>
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <Card className="!p-3">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-4">
          <label className="relative block xl:col-span-2">
            <FileSearch className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search action, user, entity, or details"
              className="surface-input pl-9"
              aria-label="Search audit logs"
            />
          </label>

          <label className="relative block">
            <Filter className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <select
              value={actionFilter}
              onChange={(event) => setActionFilter(event.target.value)}
              className="surface-select pl-9"
              aria-label="Filter audit action"
            >
              <option value="all">All actions</option>
              {availableActions.map((action) => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </label>

          <label className="relative block">
            <Clock3 className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <select
              value={dateFilter}
              onChange={(event) => setDateFilter(event.target.value)}
              className="surface-select pl-9"
              aria-label="Filter audit time range"
            >
              <option value="all">Any time</option>
              <option value="day">Last 24 hours</option>
              <option value="week">Last 7 days</option>
              <option value="month">Last 30 days</option>
            </select>
          </label>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900/70">
            <p className="section-label">Showing</p>
            <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{filteredItems.length} / {data?.total ?? 0}</p>
            <div className="mt-2 flex flex-wrap gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
              <span className="rounded-full bg-white px-2 py-1 dark:bg-slate-800">Info {infoCount}</span>
              <span className="rounded-full bg-white px-2 py-1 dark:bg-slate-800">Warnings {riskCount}</span>
              <span className="rounded-full bg-white px-2 py-1 dark:bg-slate-800">Success {successCount}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card className="!p-0">
        {isLoading && (
          <div className="space-y-2 p-3">
            {["audit-1", "audit-2", "audit-3", "audit-4", "audit-5"].map((key) => (
              <div key={key} className="rounded-xl border border-slate-200 p-4">
                <SkeletonText className="h-4 w-1/3" />
                <SkeletonText className="mt-2 h-3 w-2/3" />
                <Skeleton className="mt-3 h-5 w-24" />
              </div>
            ))}
          </div>
        )}

        {!isLoading && filteredItems.length === 0 && (
          <div className="p-4">
            <EmptyState
              title="No audit records found"
              description="Try clearing filters or expanding your search terms."
            />
          </div>
        )}

        {!isLoading && filteredItems.length > 0 && (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>User</th>
                  <th>Entity</th>
                  <th>Details</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={`${item.entity_id}-${item.timestamp}-${item.action}`}>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-200">
                          {resolveActionIcon(item.action)}
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">{item.action}</p>
                          <StatusBadge value={ACTION_TONES[item.action] ?? "info"} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1 text-xs text-slate-700 dark:text-slate-300">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        {item.user}
                      </span>
                    </td>
                    <td>
                      <p className="text-xs font-medium capitalize text-slate-700 dark:text-slate-300">{item.entity}</p>
                      <p className="font-mono text-xs text-slate-500 dark:text-slate-400">{item.entity_id}</p>
                    </td>
                    <td className="max-w-[26rem] truncate text-xs text-slate-600 dark:text-slate-300">{item.details}</td>
                    <td>
                      <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                        <Clock3 className="h-3.5 w-3.5" />
                        {formatRelativeTime(item.timestamp)}
                      </span>
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
