import React, { Fragment, useState } from "react"
import { Menu as HeadlessMenu, Transition } from "@headlessui/react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import {
  Bell,
  Bot,
  ChevronDown,
  ChartPie,
  ClipboardList,
  FileSearch,
  LayoutDashboard,
  Moon,
  PlusCircle,
  Sun,
  UserCircle2,
  UserRound,
} from "lucide-react"
import { useAuthStore, useThemeStore } from "../../store"
import {
  useLogout,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadNotificationCount,
} from "../../hooks"

const PRIMARY_NAV_LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/onboarding", label: "Workflows", icon: ClipboardList },
  { to: "/portal", label: "My Portal", icon: UserRound },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
]

const SECONDARY_NAV_LINKS = [
  { to: "/analytics", label: "Analytics", icon: ChartPie },
  { to: "/audit-logs", label: "Audit Logs", icon: FileSearch },
  { to: "/profile", label: "Profile", icon: UserCircle2 },
]

const isActivePath = (pathname: string, to: string) => pathname === to || pathname.startsWith(`${to}/`)

export const Navbar: React.FC = () => {
  const user = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.setUser)
  const themeMode = useThemeStore((state) => state.mode)
  const toggleThemeMode = useThemeStore((state) => state.toggleMode)
  const logout = useLogout()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const unreadCount = useUnreadNotificationCount(20_000)
  const notifications = useNotifications({ limit: 8, enabled: dropdownOpen, refetchInterval: 30_000 })
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  const handleLogout = async () => {
    await logout.mutateAsync()
    setUser(null)
    navigate("/login")
  }

  return (
    <nav className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 text-slate-800 shadow-[0_8px_30px_-18px_rgba(15,23,42,0.25)] backdrop-blur-xl dark:border-slate-700 dark:bg-slate-950/80 dark:text-slate-100">
      <div className="mx-auto w-[min(92vw,100rem)] px-0">
        <div className="flex min-h-16 items-center gap-4 py-3">
          <Link
            to="/dashboard"
            className="group flex items-center gap-3 font-semibold tracking-tight text-slate-900 transition-transform hover:-translate-y-0.5 dark:text-slate-100"
            aria-label="Go to dashboard"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white shadow-md shadow-slate-900/20 dark:bg-sky-500 dark:text-slate-950">
              EO
            </span>
            <span className="hidden flex-col leading-tight sm:flex">
              <span className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Enterprise</span>
              <span className="text-lg font-semibold">Onboarding Platform</span>
            </span>
          </Link>

          {user && (
            <div className="hidden min-w-0 flex-1 items-center gap-1 rounded-3xl border border-slate-200 bg-slate-50/80 p-1 dark:border-slate-700 dark:bg-slate-900/70 lg:flex">
              {PRIMARY_NAV_LINKS.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className={`rounded-2xl px-3 py-2 text-sm font-medium transition-all ${
                    isActivePath(pathname, to)
                      ? "bg-slate-900 text-white shadow-sm dark:bg-sky-500 dark:text-slate-950"
                      : "text-slate-600 hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  }`}
                >
                  <span className="inline-flex items-center gap-1.5">
                    <Icon className="h-3.5 w-3.5" />
                    <span>{label}</span>
                  </span>
                </Link>
              ))}

              <Link
                to="/employees/new"
                className="ml-1 inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm transition-transform hover:-translate-y-0.5 hover:bg-slate-800 dark:bg-sky-500 dark:text-slate-950 dark:hover:bg-sky-400"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                New Employee
              </Link>

              <HeadlessMenu as="div" className="relative ml-1">
                <HeadlessMenu.Button className="inline-flex items-center gap-1.5 rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 transition-all hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100">
                  More
                  <ChevronDown className="h-3.5 w-3.5" />
                </HeadlessMenu.Button>
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-120"
                  enterFrom="opacity-0 translate-y-1 scale-95"
                  enterTo="opacity-100 translate-y-0 scale-100"
                  leave="transition ease-in duration-90"
                  leaveFrom="opacity-100 translate-y-0 scale-100"
                  leaveTo="opacity-0 translate-y-1 scale-95"
                >
                  <HeadlessMenu.Items className="absolute right-0 z-50 mt-3 w-56 overflow-hidden rounded-3xl border border-slate-200 bg-white p-2 shadow-2xl focus:outline-none dark:border-slate-700 dark:bg-slate-900">
                    {SECONDARY_NAV_LINKS.map(({ to, label, icon: Icon }) => (
                      <HeadlessMenu.Item key={to}>
                        {({ active }) => (
                          <Link
                            to={to}
                            className={`flex items-center gap-3 rounded-2xl px-3 py-2 text-sm font-medium ${
                              active
                                ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100"
                                : "text-slate-600 dark:text-slate-300"
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                            <span>{label}</span>
                          </Link>
                        )}
                      </HeadlessMenu.Item>
                    ))}
                  </HeadlessMenu.Items>
                </Transition>
              </HeadlessMenu>
            </div>
          )}

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <button
              onClick={toggleThemeMode}
              className="rounded-2xl border border-slate-200 bg-white p-2.5 text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              aria-label="Toggle theme"
              title={themeMode === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {themeMode === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            {user ? (
              <>
                <div className="relative">
                  <button
                    onClick={() => setDropdownOpen((prev) => !prev)}
                    className="relative rounded-2xl border border-transparent p-2.5 text-slate-600 transition-colors hover:border-slate-200 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-800 dark:hover:text-white"
                    aria-label="Open notifications"
                    aria-expanded={dropdownOpen}
                  >
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5m6 0a3 3 0 11-6 0m6 0H9" />
                    </svg>
                    {(unreadCount.data?.count ?? 0) > 0 && (
                      <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-rose-500 px-1 text-center text-xs font-semibold text-white shadow-sm">
                        {(unreadCount.data?.count ?? 0) > 99 ? "99+" : unreadCount.data?.count}
                      </span>
                    )}
                  </button>

                  {dropdownOpen && (
                    <div className="absolute right-0 z-50 mt-3 w-[min(22rem,calc(100vw-2rem))] rounded-3xl border border-slate-200 bg-white p-3 text-gray-900 shadow-2xl dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
                      <div className="mb-2 flex items-center justify-between">
                        <p className="text-sm font-semibold">Notifications</p>
                        <button
                          onClick={() => markAllRead.mutate()}
                          className="text-xs font-medium text-violet-700 hover:text-violet-800 dark:text-sky-300 dark:hover:text-sky-200"
                        >
                          Mark all read
                        </button>
                      </div>

                      <div className="max-h-80 space-y-2 overflow-auto">
                        {(notifications.data?.items ?? []).length === 0 && (
                          <p className="rounded-2xl border border-dashed p-4 text-center text-sm text-gray-500 dark:text-slate-300">
                            No notifications yet.
                          </p>
                        )}
                        {(notifications.data?.items ?? []).map((item) => (
                          <button
                            key={item.id}
                            onClick={() => {
                              if (!item.is_read) {
                                markRead.mutate(item.id)
                              }
                            }}
                            className={`w-full rounded-2xl border p-3 text-left transition-all hover:-translate-y-0.5 hover:shadow-sm ${
                              item.is_read
                                ? "bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800"
                                : "border-violet-200 bg-violet-50 dark:border-blue-700 dark:bg-blue-950/40"
                            }`}
                          >
                            <p className="text-sm font-semibold">{item.title}</p>
                            <p className="mt-1 line-clamp-2 text-xs text-gray-600 dark:text-slate-300">{item.message}</p>
                          </button>
                        ))}
                      </div>

                      <Link
                        to="/notifications"
                        onClick={() => setDropdownOpen(false)}
                        className="mt-3 block rounded-xl bg-slate-900 px-3 py-2 text-center text-sm font-medium text-white hover:bg-slate-800 dark:bg-sky-500 dark:text-slate-950 dark:hover:bg-sky-400"
                      >
                        View all notifications
                      </Link>
                    </div>
                  )}
                </div>

                <span className="hidden text-sm text-slate-600 dark:text-slate-300 xl:block">{user.name || user.email}</span>
                <span className="hidden rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-200 md:block">
                  {user.role}
                </span>
                <button
                  onClick={handleLogout}
                  className="rounded-2xl bg-rose-600 px-3 py-2 text-sm font-medium text-white hover:bg-rose-700"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100">
                Login
              </Link>
            )}

            {user && (
              <button
                className="rounded-2xl p-2.5 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white lg:hidden"
                onClick={() => setMenuOpen((o) => !o)}
              >
                <span className="sr-only">Menu</span>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {menuOpen && user && (
          <div className="space-y-3 pb-4 lg:hidden">
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {PRIMARY_NAV_LINKS.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-medium ${
                    isActivePath(pathname, to)
                      ? "bg-slate-900 text-white dark:bg-sky-500 dark:text-slate-950"
                      : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              ))}
            </div>

            <Link
              to="/employees/new"
              onClick={() => setMenuOpen(false)}
              className="flex items-center gap-2 rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white dark:bg-sky-500 dark:text-slate-950"
            >
              <PlusCircle className="h-4 w-4" />
              New Employee
            </Link>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {SECONDARY_NAV_LINKS.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-medium ${
                    isActivePath(pathname, to)
                      ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100"
                      : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

