import { Suspense, lazy } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ErrorBoundary } from "react-error-boundary"
import { AuthBootstrap } from "./components/common/AuthBootstrap"
import { ProtectedRoute } from "./components/common/ProtectedRoute"
import { ToastContainer } from "./components/common/ToastContainer"
import { Layout } from "./components/layout/Layout"
import { Skeleton, SkeletonText } from "./components/common/Skeleton"
import { useNotificationStream } from "./hooks"

const LoginPage = lazy(() => import("./pages/LoginPage").then((mod) => ({ default: mod.LoginPage })))
const DashboardPage = lazy(() => import("./pages/DashboardPage").then((mod) => ({ default: mod.DashboardPage })))
const OnboardingListPage = lazy(() => import("./pages/OnboardingListPage").then((mod) => ({ default: mod.OnboardingListPage })))
const OnboardingDetailPage = lazy(() => import("./pages/OnboardingDetailPage").then((mod) => ({ default: mod.OnboardingDetailPage })))
const CreateEmployeePage = lazy(() => import("./pages/CreateEmployeePage").then((mod) => ({ default: mod.CreateEmployeePage })))
const AnalyticsDashboard = lazy(() => import("./pages/AnalyticsDashboard").then((mod) => ({ default: mod.AnalyticsDashboard })))
const ProfilePage = lazy(() => import("./pages/ProfilePage").then((mod) => ({ default: mod.ProfilePage })))
const AIAssistantPage = lazy(() => import("./pages/AIAssistantPage").then((mod) => ({ default: mod.AIAssistantPage })))
const NotificationsPage = lazy(() => import("./pages/NotificationsPage").then((mod) => ({ default: mod.NotificationsPage })))
const AuditLogsPage = lazy(() => import("./pages/AuditLogsPage").then((mod) => ({ default: mod.AuditLogsPage })))
const EmployeePortalPage = lazy(() => import("./pages/EmployeePortalPage").then((mod) => ({ default: mod.EmployeePortalPage })))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function NotificationStreamBridge() {
  useNotificationStream(true)
  return null
}

function GlobalErrorFallback({
  error,
  resetErrorBoundary,
}: Readonly<{ error: unknown; resetErrorBoundary: () => void }>) {
  const errorMessage = error instanceof Error ? error.message : "Unexpected application error."
  return (
    <div className="mx-auto mt-12 max-w-xl rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
      <h2 className="text-xl font-semibold text-rose-800">Something went wrong</h2>
      <p className="mt-2 text-sm text-rose-700">{errorMessage}</p>
      <button
        type="button"
        onClick={resetErrorBoundary}
        className="mt-4 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
      >
        Try again
      </button>
    </div>
  )
}

function PageFallback() {
  return (
    <div className="space-y-4 py-6">
      <SkeletonText className="h-8 w-52" />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-28 w-full" />
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary FallbackComponent={GlobalErrorFallback}>
        <AuthBootstrap />
        <NotificationStreamBridge />
        <ToastContainer />
        <BrowserRouter>
          <Suspense fallback={<PageFallback />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <DashboardPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/employees/new"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <CreateEmployeePage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/onboarding"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <OnboardingListPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/onboarding/:workflowId"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <OnboardingDetailPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/analytics"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <AnalyticsDashboard />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <ProfilePage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/assistant"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <AIAssistantPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/portal"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <EmployeePortalPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/notifications"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <NotificationsPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/audit-logs"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <AuditLogsPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App
