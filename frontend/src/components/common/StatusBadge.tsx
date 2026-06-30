import React from "react"

interface StatusBadgeProps {
  value: string
  className?: string
}

interface BadgeStyle {
  bg: string
  text: string
  ring: string
  dot: string
}

const STYLES: Record<string, BadgeStyle> = {
  // Workflow states
  initiated:          { bg: "bg-violet-50 dark:bg-violet-500/15",  text: "text-violet-700 dark:text-violet-300",  ring: "ring-violet-200 dark:ring-violet-500/30",  dot: "bg-violet-500" },
  hr_review:          { bg: "bg-amber-50 dark:bg-amber-500/15",    text: "text-amber-700 dark:text-amber-300",    ring: "ring-amber-200 dark:ring-amber-500/30",    dot: "bg-amber-500" },
  provisioning:       { bg: "bg-violet-50 dark:bg-violet-500/15",      text: "text-violet-700 dark:text-violet-300",      ring: "ring-blue-200 dark:ring-violet-500/30",      dot: "bg-violet-500" },
  meetings_scheduled: { bg: "bg-cyan-50 dark:bg-cyan-500/15",      text: "text-cyan-700 dark:text-cyan-300",      ring: "ring-cyan-200 dark:ring-cyan-500/30",      dot: "bg-cyan-500" },
  documents_shared:   { bg: "bg-emerald-50 dark:bg-emerald-500/15",text: "text-emerald-700 dark:text-emerald-300",ring: "ring-emerald-200 dark:ring-emerald-500/30",dot: "bg-emerald-500" },
  completed:          { bg: "bg-green-50 dark:bg-green-500/15",    text: "text-green-700 dark:text-green-300",    ring: "ring-green-200 dark:ring-green-500/30",    dot: "bg-green-500" },
  // Task statuses
  pending:            { bg: "bg-slate-100 dark:bg-slate-700/50",   text: "text-slate-600 dark:text-slate-300",    ring: "ring-slate-200 dark:ring-slate-600",       dot: "bg-slate-400" },
  in_progress:        { bg: "bg-violet-50 dark:bg-violet-500/15",      text: "text-violet-700 dark:text-violet-300",      ring: "ring-blue-200 dark:ring-violet-500/30",      dot: "bg-violet-500" },
  blocked:            { bg: "bg-rose-50 dark:bg-rose-500/15",      text: "text-rose-700 dark:text-rose-300",      ring: "ring-rose-200 dark:ring-rose-500/30",      dot: "bg-rose-500" },
  // Priority
  low:                { bg: "bg-emerald-50 dark:bg-emerald-500/15",text: "text-emerald-700 dark:text-emerald-300",ring: "ring-emerald-200 dark:ring-emerald-500/30",dot: "bg-emerald-500" },
  medium:             { bg: "bg-amber-50 dark:bg-amber-500/15",    text: "text-amber-700 dark:text-amber-300",    ring: "ring-amber-200 dark:ring-amber-500/30",    dot: "bg-amber-500" },
  high:               { bg: "bg-rose-50 dark:bg-rose-500/15",      text: "text-rose-700 dark:text-rose-300",      ring: "ring-rose-200 dark:ring-rose-500/30",      dot: "bg-rose-500" },
  // Severity
  info:               { bg: "bg-sky-50 dark:bg-sky-500/15",        text: "text-sky-700 dark:text-sky-300",        ring: "ring-sky-200 dark:ring-sky-500/30",        dot: "bg-sky-500" },
  warning:            { bg: "bg-amber-50 dark:bg-amber-500/15",    text: "text-amber-700 dark:text-amber-300",    ring: "ring-amber-200 dark:ring-amber-500/30",    dot: "bg-amber-500" },
  error:              { bg: "bg-rose-50 dark:bg-rose-500/15",      text: "text-rose-700 dark:text-rose-300",      ring: "ring-rose-200 dark:ring-rose-500/30",      dot: "bg-rose-500" },
  success:            { bg: "bg-green-50 dark:bg-green-500/15",    text: "text-green-700 dark:text-green-300",    ring: "ring-green-200 dark:ring-green-500/30",    dot: "bg-green-500" },
  // Meeting / generic
  scheduled:          { bg: "bg-violet-50 dark:bg-violet-500/15",      text: "text-violet-700 dark:text-violet-300",      ring: "ring-blue-200 dark:ring-violet-500/30",      dot: "bg-violet-500" },
  cancelled:          { bg: "bg-slate-100 dark:bg-slate-700/50",   text: "text-slate-500 dark:text-slate-400",    ring: "ring-slate-200 dark:ring-slate-600",       dot: "bg-slate-400" },
  done:               { bg: "bg-green-50 dark:bg-green-500/15",    text: "text-green-700 dark:text-green-300",    ring: "ring-green-200 dark:ring-green-500/30",    dot: "bg-green-500" },
}

const DEFAULT_STYLE: BadgeStyle = {
  bg: "bg-slate-100 dark:bg-slate-700/50",
  text: "text-slate-600 dark:text-slate-300",
  ring: "ring-slate-200 dark:ring-slate-600",
  dot: "bg-slate-400",
}

const LABELS: Record<string, string> = {
  hr_review: "HR Review",
  in_progress: "In Progress",
  meetings_scheduled: "Meetings Scheduled",
  documents_shared: "Docs Shared",
}

const formatLabel = (value: string): string =>
  LABELS[value] ?? value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())

export const StatusBadge: React.FC<StatusBadgeProps> = ({ value, className = "" }) => {
  const style = STYLES[value] ?? DEFAULT_STYLE

  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded px-1.5 py-0.5",
        "text-xs font-medium ring-1 ring-inset",
        style.bg,
        style.text,
        style.ring,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${style.dot}`} aria-hidden="true" />
      {formatLabel(value)}
    </span>
  )
}
