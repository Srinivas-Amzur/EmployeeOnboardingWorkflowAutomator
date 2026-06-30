import { useMemo, useState } from "react"
import { BadgeCheck, Mail, ShieldCheck, UserCircle2 } from "lucide-react"
import { Card } from "../components/common/Card"
import { Button } from "../components/common/Button"
import { ChangePasswordModal } from "../components/common/ChangePasswordModal"
import { useCurrentUser } from "../hooks"
import { Skeleton, SkeletonText } from "../components/common/Skeleton"

export function ProfilePage() {
  const { data: user, isLoading } = useCurrentUser()
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false)

  const initials = useMemo(() => {
    const parts = user?.name?.trim().split(/\s+/).filter(Boolean) ?? []
    if (parts.length > 0) {
      return parts.slice(0, 2).map((part) => part[0]?.toUpperCase()).join("")
    }
    return user?.email?.slice(0, 2).toUpperCase() ?? "U"
  }, [user?.email, user?.name])

  if (isLoading && !user) {
    return (
      <Card>
        <SkeletonText className="h-6 w-1/4" />
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {[
            "full-name",
            "email",
            "role",
            "status",
          ].map((key) => (
            <div key={key}>
              <SkeletonText className="h-3 w-16" />
              <Skeleton className="mt-2 h-4 w-28" />
            </div>
          ))}
        </div>
      </Card>
    )
  }

  return (
    <section className="space-y-4">
      <header className="section-shell">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="page-title">Profile</h1>
            <p className="page-subtitle">Review your account details and manage your password securely.</p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-400">
            Account settings
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.85fr)]">
        <div className="space-y-6">
          <Card className="interactive-lift">
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-xl font-bold text-white shadow-lg shadow-slate-900/20 dark:bg-sky-500 dark:text-slate-950">
                {initials}
              </div>
              <div className="space-y-2">
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{user?.name ?? "Profile"}</h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{user?.role ?? "User"}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    <BadgeCheck className="h-3.5 w-3.5" />
                    {user?.is_active ? "Active account" : "Inactive account"}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Protected by JWT session
                  </span>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Account information" className="interactive-lift">
            <div className="grid gap-2.5 md:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Full name</p>
                <p className="mt-2 text-base font-medium text-slate-900 dark:text-slate-100">{user?.name ?? "-"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Email</p>
                <p className="mt-2 inline-flex items-center gap-2 text-base font-medium text-slate-900 dark:text-slate-100">
                  <Mail className="h-4 w-4 text-slate-500" />
                  {user?.email ?? "-"}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Role</p>
                <p className="mt-2 text-base font-medium text-slate-900 dark:text-slate-100">{user?.role ?? "-"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Status</p>
                <p className="mt-2 text-base font-medium text-slate-900 dark:text-slate-100">{user?.is_active ? "Active" : "Inactive"}</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Security" className="interactive-lift space-y-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Password management
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Use a strong password with uppercase, lowercase, number, and special character requirements.
              </p>
              <div className="mt-4">
                <Button onClick={() => setIsPasswordModalOpen(true)}>Change Password</Button>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <div className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
                <UserCircle2 className="h-4 w-4 text-violet-600" />
                Session posture
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Your session is protected with httpOnly cookies and role-aware backend authorization.
              </p>
            </div>
          </Card>

          <Card title="Settings" className="interactive-lift space-y-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Accessibility and notifications</p>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Theme, notifications, and workflow preferences are managed from the global application shell.
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/70">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Support and escalation</p>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Contact HR or IT operations if your account role or access needs to be updated.
              </p>
            </div>
          </Card>
        </div>
      </div>

      <ChangePasswordModal open={isPasswordModalOpen} onClose={() => setIsPasswordModalOpen(false)} />
    </section>
  )
}