import React from "react"

interface CardProps {
  title?: string
  children: React.ReactNode
  className?: string
  /** When true, adds hover elevation effect — only for clickable/interactive cards */
  interactive?: boolean
  /** When true, removes padding — for cards containing full-bleed tables or custom layouts */
  flat?: boolean
  /** Override default padding. Use "sm" (p-4), "md" (p-5, default), "lg" (p-6), "none" (p-0) */
  padding?: "none" | "sm" | "md" | "lg"
}

const PADDING_CLASSES = {
  none: "",
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
}

export const Card: React.FC<CardProps> = ({
  title,
  children,
  className = "",
  interactive = false,
  flat = false,
  padding = "md",
}) => {
  const paddingClass = flat ? "" : PADDING_CLASSES[padding]

  return (
    <div
      className={[
        "surface-card",
        paddingClass,
        interactive
          ? "cursor-pointer transition-all duration-150 hover:-translate-y-px hover:shadow-md"
          : "transition-shadow duration-150",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {title && (
        <div className="mb-4 flex items-center gap-2.5">
          <span className="h-4 w-0.5 flex-shrink-0 rounded-full bg-violet-500" aria-hidden="true" />
          <h3 className="card-title">{title}</h3>
        </div>
      )}
      {children}
    </div>
  )
}
