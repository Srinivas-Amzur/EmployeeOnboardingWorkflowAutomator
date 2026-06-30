import { create } from "zustand"
import type { ToastMessage, User } from "../types"

interface AuthState {
  user: User | null
  isLoading: boolean
  initialized: boolean
  error: string | null
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  setInitialized: (initialized: boolean) => void
  setError: (error: string | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  initialized: false,
  error: null,
  setUser: (user) => set({ user }),
  setLoading: (loading) => set({ isLoading: loading }),
  setInitialized: (initialized) => set({ initialized }),
  setError: (error) => set({ error }),
}))

interface ToastState {
  toasts: ToastMessage[]
  addToast: (toast: Omit<ToastMessage, "id">) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        {
          id: crypto.randomUUID(),
          variant: "info",
          ...toast,
        },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    })),
}))

interface OnboardingState {
  selectedWorkflowId: string | null
  viewMode: "list" | "detail"
  setSelectedWorkflow: (id: string | null) => void
  setViewMode: (mode: "list" | "detail") => void
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  selectedWorkflowId: null,
  viewMode: "list",
  setSelectedWorkflow: (id) => set({ selectedWorkflowId: id }),
  setViewMode: (mode) => set({ viewMode: mode }),
}))

type ThemeMode = "light" | "dark"
const THEME_STORAGE_KEY = "onboarding-theme"

interface ThemeState {
  mode: ThemeMode
  toggleMode: () => void
  setMode: (mode: ThemeMode) => void
}

const detectInitialTheme = (): ThemeMode => {
  const stored = globalThis.localStorage.getItem(THEME_STORAGE_KEY)
  if (stored === "dark" || stored === "light") {
    return stored
  }
  return globalThis.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light"
}

const applyThemeClass = (mode: ThemeMode) => {
  document.documentElement.classList.toggle("dark", mode === "dark")
}

export const useThemeStore = create<ThemeState>((set) => ({
  mode: detectInitialTheme(),
  setMode: (mode) => {
    globalThis.localStorage.setItem(THEME_STORAGE_KEY, mode)
    applyThemeClass(mode)
    set({ mode })
  },
  toggleMode: () =>
    set((state) => {
      const nextMode: ThemeMode = state.mode === "dark" ? "light" : "dark"
      globalThis.localStorage.setItem(THEME_STORAGE_KEY, nextMode)
      applyThemeClass(nextMode)
      return { mode: nextMode }
    }),
}))
