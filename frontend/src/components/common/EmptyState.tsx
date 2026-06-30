import React from "react"

interface EmptyStateProps {
  title: string
  description: string
  action?: React.ReactNode
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action }) => {
  return (
    <div className="rounded-3xl border border-dashed border-slate-300/80 bg-slate-50/80 p-8 text-center dark:border-slate-700 dark:bg-slate-900/60">
      <p className="text-base font-semibold text-slate-800 dark:text-slate-100">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-600 dark:text-slate-300">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
