import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "../components/common/Button"
import { Card } from "../components/common/Card"
import { useLogin } from "../hooks"
import { useAuthStore, useToastStore } from "../store"

const REMEMBER_KEY = "onboarding-remembered-email"

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)

  const login = useLogin()
  const setUser = useAuthStore((state) => state.setUser)
  const setInitialized = useAuthStore((state) => state.setInitialized)
  const setLoading = useAuthStore((state) => state.setLoading)
  const addToast = useToastStore((state) => state.addToast)
  const navigate = useNavigate()

  useEffect(() => {
    const remembered = globalThis.localStorage.getItem(REMEMBER_KEY)
    if (!remembered) return
    setEmail(remembered)
    setRememberMe(true)
  }, [])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError("")

    try {
      setLoading(true)
      const response = await login.mutateAsync({ email, password })
      setUser(response.user)
      setInitialized(true)

      if (rememberMe) {
        globalThis.localStorage.setItem(REMEMBER_KEY, email)
      } else {
        globalThis.localStorage.removeItem(REMEMBER_KEY)
      }

      addToast({ title: "Signed in", description: "Your session is active.", variant: "success" })
      navigate("/dashboard")
    } catch (caughtError: unknown) {
      let detail = "Login failed"
      if (
        typeof caughtError === "object" &&
        caughtError !== null &&
        "response" in caughtError &&
        typeof (caughtError as { response?: { data?: { detail?: unknown } } }).response?.data?.detail === "string"
      ) {
        detail = (caughtError as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? detail
      }
      setError(detail)
      addToast({ title: "Login failed", description: detail, variant: "error" })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = () => {
    const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
    globalThis.location.href = `${apiBase}/auth/google/login`
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#F8FAFC_0%,#F1F5F9_100%)] p-4 md:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] w-full max-w-6xl grid-cols-1 overflow-hidden rounded-3xl border border-slate-200 bg-white/80 shadow-2xl backdrop-blur-sm md:min-h-[calc(100vh-4rem)] md:grid-cols-2">
        <section className="relative hidden overflow-hidden bg-slate-900 p-10 text-slate-100 md:flex md:flex-col md:justify-between">
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(2,6,23,0.2)_0%,rgba(2,6,23,0.55)_100%)]" />
          <div className="relative">
            <p className="inline-flex rounded-full border border-sky-300/40 bg-sky-400/10 px-3 py-1 text-xs font-semibold tracking-wide text-sky-200">
              Enterprise Onboarding Platform
            </p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight">Launch every new hire with predictable, auditable workflows.</h1>
            <p className="mt-4 max-w-md text-sm text-slate-200/85">
              Coordinate HR, IT provisioning, orientation, documents, and AI-powered onboarding support from one control plane.
            </p>
          </div>

          <ul className="relative space-y-3 text-sm text-slate-200/90">
            <li className="rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3">Workflow orchestration with state-trace timelines</li>
            <li className="rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3">AI assistant grounded by onboarding policy documents</li>
            <li className="rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3">Enterprise notifications, auditability, and analytics</li>
          </ul>
        </section>

        <section className="flex items-center justify-center p-5 sm:p-8">
          <Card className="w-full max-w-md border-slate-200/80 shadow-none">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Sign in</h2>
            <p className="mt-1 text-sm text-slate-600">Access the onboarding operations dashboard.</p>

            {error && (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div>
                <label htmlFor="login-email" className="mb-2 block text-sm font-medium text-slate-700">Work Email</label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
                  placeholder="you@company.com"
                  required
                />
              </div>

              <div>
                <label htmlFor="login-password" className="mb-2 block text-sm font-medium text-slate-700">Password</label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2.5 pr-16 text-sm"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-2 my-auto h-8 rounded-md px-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between gap-3">
                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(event) => setRememberMe(event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  <span>Remember email</span>
                </label>
                <button
                  type="button"
                  onClick={() => addToast({ title: "Coming soon", description: "Forgot password flow will be added in the next phase.", variant: "info" })}
                  className="text-sm font-medium text-violet-700 hover:text-violet-800"
                >
                  Forgot password?
                </button>
              </div>

              <Button type="submit" variant="primary" isLoading={login.isPending} className="w-full">
                Sign in
              </Button>

              <button
                type="button"
                onClick={handleGoogleSignIn}
                className="flex w-full items-center justify-center gap-3 rounded-lg border px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                style={{ borderColor: "var(--surface-border)" }}
              >
                <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4" />
                  <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853" />
                  <path d="M3.964 10.71C3.784 10.17 3.682 9.593 3.682 9s.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05" />
                  <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335" />
                </svg>
                Continue with Google
              </button>
            </form>
          </Card>
        </section>
      </div>
    </main>
  )
}
