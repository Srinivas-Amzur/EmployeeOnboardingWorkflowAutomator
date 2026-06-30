import React from "react"
import { X } from "lucide-react"
import { Link, useLocation } from "react-router-dom"
import { useAuthStore } from "../../store"
import { isActivePath, SIDEBAR_SECTIONS } from "./navigation"

interface EnterpriseSidebarProps {
  collapsed: boolean
  mobileOpen: boolean
  onToggleCollapse: () => void
  onCloseMobile: () => void
}

function getInitials(name: string): string {
  return name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()
}

function getAvatarColor(str: string): string {
  const colors = ["#7c3aed", "#059669", "#d97706", "#dc2626", "#0284c7", "#9333ea"]
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
}

const SIDEBAR_W = 88

export const EnterpriseSidebar: React.FC<EnterpriseSidebarProps> = ({
  mobileOpen,
  onCloseMobile,
}) => {
  const { pathname } = useLocation()
  const user = useAuthStore((state) => state.user)

  const displayName = user?.name || user?.email || "User"
  const initials    = getInitials(displayName)
  const avatarColor = getAvatarColor(displayName)

  // Flat list from all sections for the narrow rail
  const allItems = SIDEBAR_SECTIONS.flatMap((s) => s.items)

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <button
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-label="Close sidebar"
        />
      )}

      <aside
        className={[
          "fixed inset-y-0 left-0 z-50 flex flex-col",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          "transition-transform duration-200",
        ].join(" ")}
        style={{
          width: `${SIDEBAR_W}px`,
          background: "linear-gradient(180deg, #1e1b4b 0%, #1a1a2e 100%)",
          borderRight: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {/* Logo mark */}
        <div
          className="flex h-14 flex-shrink-0 items-center justify-center"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}
        >
          <Link to="/dashboard" onClick={onCloseMobile} title="Dashboard">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl shadow-lg"
              style={{ background: "linear-gradient(135deg, #5b35d9, #7c3aed)" }}>
              <svg width="20" height="20" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <circle cx="6"  cy="6"  r="3" fill="white" fillOpacity="0.95" />
                <circle cx="12" cy="12" r="3" fill="white" fillOpacity="0.55" />
                <line x1="6" y1="9" x2="12" y2="9" stroke="white" strokeOpacity="0.75" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </span>
          </Link>

          {/* Mobile close */}
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close sidebar"
            className="absolute right-1 top-4 rounded p-1 text-white/40 hover:text-white lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Nav rail — icon above label */}
        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 scrollbar-thin">
          {allItems.map(({ to, label, icon: Icon }) => {
            const active = isActivePath(pathname, to)
            return (
              <Link
                key={to + label}
                to={to}
                onClick={onCloseMobile}
                title={label}
                className="relative mx-1 mb-0.5 flex flex-col items-center justify-center gap-1 rounded-xl py-2.5 transition-all duration-150"
                style={
                  active
                    ? { background: "#ffffff", color: "#5b35d9" }
                    : { color: "rgba(255,255,255,0.50)" }
                }
                onMouseEnter={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)"
                    ;(e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.90)"
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.background = ""
                    ;(e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.50)"
                  }
                }}
              >
                {/* Active left accent bar */}
                {active && (
                  <span
                    className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
                    style={{ background: "#5b35d9" }}
                  />
                )}
                <Icon className="h-[18px] w-[18px] flex-shrink-0" />
                <span className="w-full break-words px-1 text-center"
                  style={{ fontSize: "9.5px", fontWeight: active ? 700 : 500, letterSpacing: "0.01em", lineHeight: 1.2 }}>
                  {label}
                </span>
              </Link>
            )
          })}
        </nav>

        {/* User avatar */}
        <div
          className="flex flex-shrink-0 items-center justify-center py-3"
          style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}
        >
          <Link to="/profile" title={displayName} onClick={onCloseMobile}>
            <span
              className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white shadow"
              style={{ background: avatarColor }}
            >
              {initials}
            </span>
          </Link>
        </div>
      </aside>
    </>
  )
}
