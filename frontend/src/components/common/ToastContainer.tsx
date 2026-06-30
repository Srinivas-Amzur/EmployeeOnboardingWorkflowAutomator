import { useEffect } from "react"
import { useToastStore } from "../../store"

const variantClasses = {
  success: "border-green-200 bg-green-50 text-green-900",
  error: "border-red-200 bg-red-50 text-red-900",
  info: "border-violet-200 bg-violet-50 text-blue-900",
}

export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts)
  const removeToast = useToastStore((state) => state.removeToast)

  useEffect(() => {
    if (toasts.length === 0) {
      return
    }

    const timers = toasts.map((toast) =>
      globalThis.setTimeout(() => removeToast(toast.id), 3500)
    )

    return () => {
      timers.forEach((timer) => globalThis.clearTimeout(timer))
    }
  }, [removeToast, toasts])

  return (
    <div className="fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`animate-[fadeIn_220ms_ease] rounded-2xl border px-4 py-3 shadow-xl ${variantClasses[toast.variant ?? "info"]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold">{toast.title}</p>
              {toast.description && <p className="mt-1 text-sm opacity-90">{toast.description}</p>}
            </div>
            <button
              type="button"
              className="rounded-md px-2 py-1 text-xs font-medium opacity-80 hover:bg-black/5 hover:opacity-100"
              onClick={() => removeToast(toast.id)}
            >
              Close
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}