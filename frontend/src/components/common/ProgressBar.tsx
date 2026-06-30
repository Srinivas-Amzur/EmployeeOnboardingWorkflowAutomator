import React from "react"

interface ProgressBarProps {
  value: number
  label?: string
  className?: string
  tone?: "primary" | "success" | "warning"
}

const toneClasses: Record<NonNullable<ProgressBarProps["tone"]>, string> = {
  primary: "from-blue-500 to-indigo-500",
  success: "from-emerald-500 to-teal-500",
  warning: "from-amber-500 to-orange-500",
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  className = "",
  tone = "primary",
}) => {
  const clamped = Math.min(100, Math.max(0, value))

  return (
    <div className={`space-y-1 ${className}`}>
      {label !== undefined && (
        <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
          <span>{label}</span>
          <span>{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-700/80">
        <div
          className={`h-full rounded-full bg-gradient-to-r transition-all duration-500 ${toneClasses[tone]}`}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={Math.round(clamped)}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
}
