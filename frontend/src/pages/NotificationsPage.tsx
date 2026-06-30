import React, { useMemo, useState } from "react"
import { Bell, CheckCircle2, Sparkles, TriangleAlert } from "lucide-react"
import { Button } from "../components/common/Button"
import { EmptyState } from "../components/common/EmptyState"
import { Skeleton } from "../components/common/Skeleton"
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from "../hooks"
import { formatRelativeTime } from "../lib/time"

function resolveTemporalBucket(value: string): "Today" | "Yesterday" | "Earlier" {
  const now = new Date()
  const created = new Date(value)

  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterdayStart = todayStart - 24 * 60 * 60 * 1000
  const createdTs = created.getTime()

  if (createdTs >= todayStart) return "Today"
  if (createdTs >= yesterdayStart) return "Yesterday"
  return "Earlier"
}

const resolveSeverity = (type: string): "info" | "warning" | "error" | "success" => {
  if (type.includes("error") || type.includes("failed") || type.includes("escalation")) return "error"
  if (type.includes("warning") || type.includes("overdue")) return "warning"
  if (type.includes("completed") || type.includes("success")) return "success"
  return "info"
}

const resolveCategory = (type: string): "workflow" | "task" | "ai" | "system" => {
  if (type.includes("ai") || type.includes("rag")) return "ai"
  if (type.includes("task")) return "task"
  if (type.includes("workflow") || type.includes("escalation") || type.includes("meeting")) return "workflow"
  return "system"
}

const SEVERITY_STYLES: Record<string, { dot: string; border: string; icon: string }> = {
  error:   { dot: "bg-rose-500",    border: "border-l-rose-500",    icon: "text-rose-500" },
  warning: { dot: "bg-amber-500",   border: "border-l-amber-500",   icon: "text-amber-500" },
  success: { dot: "bg-emerald-500", border: "border-l-emerald-500", icon: "text-emerald-500" },
  info:    { dot: "bg-sky-500",     border: "border-l-sky-500",     icon: "text-sky-500" },
}

function resolveIcon(type: string): React.ReactNode {
  if (type.includes("completed") || type.includes("success")) return <CheckCircle2 className="h-3.5 w-3.5" />
  if (type.includes("escalation") || type.includes("warning") || type.includes("overdue")) return <TriangleAlert className="h-3.5 w-3.5" />
  if (type.includes("ai") || type.includes("rag")) return <Sparkles className="h-3.5 w-3.5" />
  return <Bell className="h-3.5 w-3.5" />
}

const CATEGORY_FILTERS = [
  { label: "All", value: "all" },
  { label: "Workflow", value: "workflow" },
  { label: "Tasks", value: "task" },
  { label: "AI", value: "ai" },
  { label: "System", value: "system" },
] as const

export const NotificationsPage: React.FC = () => {
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<"all" | "workflow" | "task" | "ai" | "system">("all")
  const { data, isLoading } = useNotifications({ limit: 100, unread_only: showUnreadOnly })
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  const items = data?.items ?? []
  const unreadCount = data?.unread_count ?? 0

  const filteredItems = useMemo(
    () => items.filter((item) => categoryFilter === "all" || resolveCategory(item.notification_type) === categoryFilter),
    [categoryFilter, items],
  )

  const groupedByDate = useMemo(() => {
    const groups: Record<string, typeof filteredItems> = {}
    for (const item of filteredItems) {
      const dateKey = resolveTemporalBucket(item.created_at)
      groups[dateKey] = groups[dateKey] ? [...groups[dateKey], item] : [item]
    }
    return groups
  }, [filteredItems])

  const orderedBuckets = ["Today", "Yesterday", "Earlier"].filter((bucket) => groupedByDate[bucket]?.length)

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: items.length }
    for (const item of items) {
      const cat = resolveCategory(item.notification_type)
      counts[cat] = (counts[cat] ?? 0) + 1
    }
    return counts
  }, [items])

  const severityCounts = useMemo(() => {
    const counts: Record<"info" | "warning" | "error" | "success", number> = {
      info: 0,
      warning: 0,
      error: 0,
      success: 0,
    }
    for (const item of items) {
      counts[resolveSeverity(item.notification_type)] += 1
    }
    return counts
  }, [items])

  return (
    <section className="space-y-3">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">{filteredItems.length} events | {unreadCount} unread</p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => setShowUnreadOnly((v) => !v)}>
            {showUnreadOnly ? "All" : "Unread only"}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => markAllRead.mutate()} disabled={unreadCount === 0 || markAllRead.isPending}>
            Mark all read
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 xl:grid-cols-4">
        {[
          { label: "Errors", value: severityCounts.error, tone: "text-rose-600 dark:text-rose-300", bg: "bg-rose-50 dark:bg-rose-500/10" },
          { label: "Warnings", value: severityCounts.warning, tone: "text-amber-600 dark:text-amber-300", bg: "bg-amber-50 dark:bg-amber-500/10" },
          { label: "Success", value: severityCounts.success, tone: "text-emerald-600 dark:text-emerald-300", bg: "bg-emerald-50 dark:bg-emerald-500/10" },
          { label: "Unread", value: unreadCount, tone: "text-sky-600 dark:text-sky-300", bg: "bg-sky-50 dark:bg-sky-500/10" },
        ].map((metric) => (
          <div key={metric.label} className="kpi-card flex items-center justify-between">
            <div>
              <p className="section-label">{metric.label}</p>
              <p className={`text-2xl font-bold tabular-nums ${metric.tone}`}>{metric.value}</p>
            </div>
            <span className={`h-9 w-9 rounded-xl ${metric.bg}`} aria-hidden="true" />
          </div>
        ))}
      </div>

      <div className="flex gap-4">
        {/* Category sidebar */}
        <aside className="hidden w-48 flex-shrink-0 space-y-1 lg:block">
          <p className="section-label px-2 pb-1">Filter</p>
          {CATEGORY_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setCategoryFilter(f.value)}
              className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                categoryFilter === f.value
                  ? "bg-slate-900 text-white dark:bg-sky-500 dark:text-slate-950"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <span>{f.label}</span>
              <span className={`rounded-full px-1.5 text-xs font-bold ${categoryFilter === f.value ? "bg-white/20 text-white" : "text-slate-400"}`}>
                {categoryCounts[f.value] ?? 0}
              </span>
            </button>
          ))}
        </aside>

        {/* Mobile category chips */}
        <div className="flex flex-wrap gap-2 lg:hidden">
          {CATEGORY_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setCategoryFilter(f.value)}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                categoryFilter === f.value
                  ? "bg-slate-900 text-white dark:bg-sky-500 dark:text-slate-950"
                  : "border border-slate-200 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              }`}
            >
              {f.label} {categoryCounts[f.value] ? `(${categoryCounts[f.value]})` : ""}
            </button>
          ))}
        </div>

        {/* Timeline */}
        <div className="min-w-0 flex-1">
          {isLoading && (
            <div className="space-y-2">
              {["sk1","sk2","sk3","sk4","sk5"].map((k) => <Skeleton key={k} className="h-16 rounded-xl" />)}
            </div>
          )}

          {!isLoading && filteredItems.length === 0 && (
            <EmptyState title="No notifications" description="Events from workflows and tasks will appear here." />
          )}

          {!isLoading && filteredItems.length > 0 && (
            <div className="space-y-6">
              {orderedBuckets.map((dateKey) => {
                const dateItems = groupedByDate[dateKey]
                if (!dateItems) return null

                return (
                <div key={dateKey}>
                  <div className="sticky top-14 z-10 mb-3 flex items-center gap-3">
                    <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
                    <span className="rounded-full border border-slate-200 bg-white px-3 py-0.5 text-xs font-semibold text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">{dateKey}</span>
                    <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
                  </div>

                  <div className="relative space-y-px pl-5">
                    {/* Vertical timeline line */}
                    <div className="absolute left-1.5 top-0 h-full w-px bg-slate-200 dark:bg-slate-700" />

                    {dateItems.map((item) => {
                      const severity = resolveSeverity(item.notification_type)
                      const style = SEVERITY_STYLES[severity]
                      const icon = resolveIcon(item.notification_type)

                      return (
                        <article
                          key={item.id}
                          className={`relative rounded-xl border-l-2 bg-white py-3 pl-4 pr-3 shadow-sm transition-all duration-100 hover:shadow-md dark:bg-slate-900/80 ${style.border} ${item.is_read ? "opacity-70 hover:opacity-100" : ""}`}
                        >
                          {/* Timeline dot */}
                          <span className={`absolute -left-[1.125rem] top-4 flex h-4 w-4 items-center justify-center rounded-full border-2 border-white bg-white dark:border-slate-900 dark:bg-slate-900 ${style.icon}`}>
                            {icon}
                          </span>

                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                {!item.is_read && <span className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${style.dot}`} />}
                                <p className={`text-sm font-semibold text-slate-900 dark:text-slate-100 ${item.is_read ? "font-medium" : ""}`}>{item.title}</p>
                              </div>
                              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-300">{item.message}</p>
                              <p className="mt-1.5 text-xs text-slate-400">{formatRelativeTime(item.created_at)}</p>
                            </div>
                            {!item.is_read && (
                              <button
                                onClick={() => markRead.mutate(item.id)}
                                className="flex-shrink-0 rounded-lg px-2 py-1 text-xs font-medium text-violet-600 hover:bg-violet-50 hover:text-violet-800 dark:text-sky-400 dark:hover:bg-blue-900/20"
                              >
                                Read
                              </button>
                            )}
                          </div>
                        </article>
                      )
                    })}
                  </div>
                </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
