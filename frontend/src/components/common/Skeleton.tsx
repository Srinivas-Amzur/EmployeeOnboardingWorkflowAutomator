import React from "react"

interface SkeletonProps {
  className?: string
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = "" }) => {
  return <div className={`animate-pulse rounded-2xl bg-gradient-to-r from-slate-200/70 via-slate-100/90 to-slate-200/70 dark:from-slate-800/70 dark:via-slate-700/90 dark:to-slate-800/70 ${className}`} aria-hidden="true" />
}

export const SkeletonText: React.FC<SkeletonProps> = ({ className = "" }) => {
  return <div className={`animate-pulse rounded-xl bg-gradient-to-r from-slate-200/70 via-slate-100/90 to-slate-200/70 dark:from-slate-800/70 dark:via-slate-700/90 dark:to-slate-800/70 h-4 ${className}`} aria-hidden="true" />
}
