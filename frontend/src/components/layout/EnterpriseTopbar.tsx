import React, { useEffect, useRef, useState } from "react"
import { Bell, ChevronDown, LogOut, Menu, Moon, Search, Sun, User } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"
import { useAuthStore, useThemeStore } from "../../store"
import {
  useLogout,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadNotificationCount,
} from "../../hooks"

function useClickOutside(ref: React.RefObject<HTMLElement | null>, handler: () => void) {
  useEffect(() => {
    const fn = (e: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(e.target as Node)) return
      handler()
    }
    document.addEventListener("mousedown", fn)
    document.addEventListener("touchstart", fn)
    return () => {
      document.removeEventListener("mousedown", fn)
      document.removeEventListener("touchstart", fn)
    }
  }, [ref, handler])
}

function getInitials(str: string) {
  return str.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()
}

function getAvatarGradient(str: string) {
  const COLORS = ["#7c3aed,#5b35d9", "#059669,#047857", "#d97706,#b45309", "#dc2626,#b91c1c"]
  let h = 0
  for (let i = 0; i < str.length; i++) h = str.charCodeAt(i) + ((h << 5) - h)
  const [from, to] = COLORS[Math.abs(h) % COLORS.length].split(",")
  return `linear-gradient(135deg, ${from}, ${to})`
}

interface EnterpriseTopbarProps {
  onOpenSidebar: () => void
}

export const EnterpriseTopbar: React.FC<EnterpriseTopbarProps> = ({ onOpenSidebar }) => {
  const [notifOpen,    setNotifOpen]    = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)
  const userRef  = useRef<HTMLDivElement>(null)

  const user        = useAuthStore((s) => s.user)
  const setUser     = useAuthStore((s) => s.setUser)
  const themeMode   = useThemeStore((s) => s.mode)
  const toggleTheme = useThemeStore((s) => s.toggleMode)
  const logout      = useLogout()
  const navigate    = useNavigate()

  const unreadCount   = useUnreadNotificationCount(20_000)
  const notifications = useNotifications({ limit: 8, enabled: notifOpen, refetchInterval: 30_000 })
  const markRead      = useMarkNotificationRead()
  const markAllRead   = useMarkAllNotificationsRead()

  useClickOutside(notifRef, () => setNotifOpen(false))
  useClickOutside(userRef,  () => setUserMenuOpen(false))

  const handleLogout = async () => {
    setUserMenuOpen(false)
    await logout.mutateAsync()
    setUser(null)
    navigate("/login")
  }

  const displayName = user?.name || user?.email || "User"
  const initials    = getInitials(displayName)
  const avatarStyle = { background: getAvatarGradient(displayName) }
  const unread      = unreadCount.data?.count ?? 0

  return (
    <header
      className="sticky top-0 z-30 flex h-14 items-center gap-3 px-4 sm:px-5"
      style={{
        background: "linear-gradient(90deg, #3b1fa8 0%, #5b35d9 55%, #6a42e0 100%)",
        boxShadow: "0 2px 12px 0 rgba(59,31,168,0.35)",
      }}
    >
      {/* Mobile hamburger */}
      <button
        type="button"
        onClick={onOpenSidebar}
        aria-label="Open navigation"
        className="flex-shrink-0 rounded-lg p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Logo + app name â€” desktop */}
      <Link
        to="/dashboard"
        className="hidden flex-shrink-0 items-center gap-2.5 lg:flex"
      >
        <span
          className="flex h-8 w-8 items-center justify-center rounded-lg shadow-inner"
          style={{ background: "rgba(255,255,255,0.18)" }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <circle cx="6"  cy="6"  r="3" fill="white" fillOpacity="0.95" />
            <circle cx="12" cy="12" r="3" fill="white" fillOpacity="0.55" />
            <line x1="6" y1="9" x2="12" y2="9" stroke="white" strokeOpacity="0.75" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </span>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-white/50">Amzur Infotech</p>
          <p className="text-sm font-bold leading-tight text-white">Onboarding Hub</p>
        </div>
      </Link>

      {/* Centre search â€” Keka style */}
      <div className="mx-auto flex w-full max-w-md items-center gap-2 rounded-full px-4 py-2"
        style={{ background: "rgba(255,255,255,0.14)", border: "1px solid rgba(255,255,255,0.18)" }}>
        <Search className="h-3.5 w-3.5 flex-shrink-0 text-white/60" />
        <span className="flex-1 text-sm text-white/55 select-none">
          Search employees or actions…
        </span>
        <kbd className="flex-shrink-0 rounded bg-white/15 px-1.5 py-0.5 text-[10px] font-medium text-white/50">
          Alt+K
        </kbd>
      </div>

      {/* Right actions */}
      <div className="flex flex-shrink-0 items-center gap-1">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          aria-label={themeMode === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          className="rounded-lg p-2 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
        >
          {themeMode === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* Notification bell */}
        {user && (
          <div className="relative" ref={notifRef}>
            <button
              onClick={() => setNotifOpen((v) => !v)}
              aria-label="Open notifications"
              aria-expanded={notifOpen}
              className="relative rounded-lg p-2 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              <Bell className="h-4 w-4" />
              {unread > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white leading-none">
                  {unread > 99 ? "99+" : unread}
                </span>
              )}
            </button>

            {notifOpen && (
              <div
                className="absolute right-0 z-50 mt-2 w-[min(22rem,calc(100vw-1rem))] overflow-hidden rounded-xl border shadow-elevation-3"
                style={{ borderColor: "var(--surface-border)", backgroundColor: "var(--surface-base)" }}
              >
                <div className="flex items-center justify-between border-b px-3 py-2.5"
                  style={{ borderColor: "var(--surface-border)" }}>
                  <p className="section-label">Notifications</p>
                  <button
                    onClick={() => markAllRead.mutate()}
                    className="text-xs font-medium text-violet-600 hover:text-violet-700 dark:text-violet-400"
                  >
                    Mark all read
                  </button>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {(notifications.data?.items ?? []).length === 0 && (
                    <p className="p-6 text-center text-sm text-slate-500 dark:text-slate-400">No notifications</p>
                  )}
                  {(notifications.data?.items ?? []).map((item) => (
                    <button
                      key={item.id}
                      onClick={() => { if (!item.is_read) markRead.mutate(item.id) }}
                      className={[
                        "w-full border-b px-3 py-2.5 text-left text-sm transition-colors last:border-b-0",
                        item.is_read
                          ? "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                          : "bg-violet-50 hover:bg-violet-100/70 dark:bg-violet-500/10 dark:hover:bg-violet-500/15",
                      ].join(" ")}
                      style={{ borderColor: "var(--surface-border)" }}
                    >
                      <div className="flex items-start gap-2">
                        {!item.is_read && (
                          <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-violet-500" />
                        )}
                        <div className="min-w-0">
                          <p className="truncate font-medium text-slate-900 dark:text-slate-100">{item.title}</p>
                          <p className="mt-0.5 line-clamp-1 text-xs text-slate-500 dark:text-slate-400">{item.message}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                <div className="border-t p-2" style={{ borderColor: "var(--surface-border)" }}>
                  <Link
                    to="/notifications"
                    onClick={() => setNotifOpen(false)}
                    className="block rounded-md px-3 py-1.5 text-center text-xs font-medium text-violet-600 transition-colors hover:bg-violet-50 dark:text-violet-400 dark:hover:bg-violet-500/10"
                  >
                    View all notifications
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {/* User avatar + dropdown */}
        {user && (
          <div className="relative" ref={userRef}>
            <button
              onClick={() => setUserMenuOpen((v) => !v)}
              aria-label="Open user menu"
              aria-expanded={userMenuOpen}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-white/10"
            >
              <span
                className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow"
                style={avatarStyle}
              >
                {initials}
              </span>
              <span className="hidden max-w-28 truncate text-sm font-semibold text-white md:block">
                {displayName}
              </span>
              <ChevronDown className="hidden h-3.5 w-3.5 text-white/60 md:block" />
            </button>

            {userMenuOpen && (
              <div
                className="absolute right-0 z-50 mt-1.5 w-52 overflow-hidden rounded-xl border shadow-elevation-3"
                style={{ borderColor: "var(--surface-border)", backgroundColor: "var(--surface-base)" }}
              >
                <div className="border-b px-3 py-2.5" style={{ borderColor: "var(--surface-border)" }}>
                  <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{displayName}</p>
                  <p className="truncate text-xs capitalize text-slate-500 dark:text-slate-400">{user.role}</p>
                </div>
                <div className="p-1">
                  <Link
                    to="/profile"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    <User className="h-4 w-4 text-slate-400" />
                    Profile & Settings
                  </Link>
                </div>
                <div className="border-t p-1" style={{ borderColor: "var(--surface-border)" }}>
                  <button
                    onClick={handleLogout}
                    disabled={logout.isPending}
                    className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-500/10"
                  >
                    <LogOut className="h-4 w-4" />
                    {logout.isPending ? "Signing out…" : "Sign out"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
