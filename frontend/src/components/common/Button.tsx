import React from "react"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost" | "danger-ghost"
  size?: "xs" | "sm" | "md" | "lg"
  isLoading?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  isLoading = false,
  children,
  disabled,
  className = "",
  ...props
}) => {
  const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
    primary:
      "bg-violet-600 text-white shadow-sm hover:bg-violet-700 dark:bg-violet-500 dark:hover:bg-violet-400",
    secondary:
      "bg-slate-100 text-slate-700 shadow-sm hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
    outline:
      "border border-slate-300 bg-white text-slate-700 hover:border-violet-400 hover:bg-violet-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800",
    danger:
      "bg-rose-600 text-white shadow-sm hover:bg-rose-700",
    ghost:
      "bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100",
    "danger-ghost":
      "bg-transparent text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:hover:bg-rose-500/10",
  }

  const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
    xs: "h-6 px-2 text-xs gap-1",
    sm: "h-8 px-3 py-1.5 text-[13px] gap-1.5",
    md: "h-9 px-4 py-2 text-sm gap-2",
    lg: "h-10 px-5 py-2.5 text-[15px] gap-2",
  }

  return (
    <button
      className={[
        "inline-flex items-center justify-center rounded-lg font-medium",
        "transition-colors duration-150 active:translate-y-px",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white",
        "dark:focus-visible:ring-sky-400 dark:focus-visible:ring-offset-slate-950",
        variantClasses[variant],
        sizeClasses[size],
        isLoading || disabled ? "cursor-not-allowed opacity-60" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      disabled={isLoading || disabled}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading && (
        <span
          className="h-3.5 w-3.5 flex-shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent opacity-70"
          aria-hidden="true"
        />
      )}
      {children}
    </button>
  )
}
