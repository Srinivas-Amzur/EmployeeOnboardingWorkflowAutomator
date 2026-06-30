import { Fragment, useMemo, useState } from "react"
import { Dialog, Transition } from "@headlessui/react"
import { Button } from "./Button"
import { useChangePassword } from "../../hooks"
import { useToastStore } from "../../store"

interface ChangePasswordModalProps {
  open: boolean
  onClose: () => void
}

interface FormState {
  current_password: string
  new_password: string
  confirm_password: string
}

const initialForm: FormState = {
  current_password: "",
  new_password: "",
  confirm_password: "",
}

function validatePassword(form: FormState) {
  const errors: Partial<FormState> = {}

  if (!form.current_password) {
    errors.current_password = "Current password is required"
  }
  if (form.new_password.length < 8) {
    errors.new_password = "Minimum 8 characters"
  } else if (!/[A-Z]/.test(form.new_password)) {
    errors.new_password = "At least one uppercase letter required"
  } else if (!/[a-z]/.test(form.new_password)) {
    errors.new_password = "At least one lowercase letter required"
  } else if (!/\d/.test(form.new_password)) {
    errors.new_password = "At least one number required"
  } else if (!/[^A-Za-z0-9]/.test(form.new_password)) {
    errors.new_password = "At least one special character required"
  }

  if (form.confirm_password !== form.new_password) {
    errors.confirm_password = "Passwords must match"
  }

  return errors
}

export function ChangePasswordModal({ open, onClose }: ChangePasswordModalProps) {
  const [form, setForm] = useState<FormState>(initialForm)
  const [errors, setErrors] = useState<Partial<FormState>>({})
  const changePassword = useChangePassword()
  const addToast = useToastStore((state) => state.addToast)

  const passwordChecklist = useMemo(
    () => [
      { label: "8+ characters", ok: form.new_password.length >= 8 },
      { label: "Uppercase letter", ok: /[A-Z]/.test(form.new_password) },
      { label: "Lowercase letter", ok: /[a-z]/.test(form.new_password) },
      { label: "Number", ok: /\d/.test(form.new_password) },
      { label: "Special character", ok: /[^A-Za-z0-9]/.test(form.new_password) },
    ],
    [form.new_password]
  )

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleClose = () => {
    if (changePassword.isPending) {
      return
    }
    setForm(initialForm)
    setErrors({})
    onClose()
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const nextErrors = validatePassword(form)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      return
    }

    try {
      const response = await changePassword.mutateAsync(form)
      addToast({ title: "Password updated", description: response.message, variant: "success" })
      handleClose()
    } catch (error: any) {
      const detail = error.response?.data?.detail || "Unable to update password"
      addToast({ title: "Password update failed", description: detail, variant: "error" })
    }
  }

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/40" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4"
              enterTo="opacity-100 translate-y-0"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0"
              leaveTo="opacity-0 translate-y-4"
            >
              <Dialog.Panel className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
                <Dialog.Title className="text-xl font-semibold text-gray-900">
                  Change Password
                </Dialog.Title>
                <p className="mt-2 text-sm text-gray-500">
                  Confirm your current password, then choose a stronger replacement.
                </p>

                <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">Current password</label>
                    <input
                      type="password"
                      name="current_password"
                      value={form.current_password}
                      onChange={handleChange}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                    />
                    {errors.current_password && <p className="mt-1 text-xs text-red-600">{errors.current_password}</p>}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">New password</label>
                    <input
                      type="password"
                      name="new_password"
                      value={form.new_password}
                      onChange={handleChange}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                    />
                    {errors.new_password && <p className="mt-1 text-xs text-red-600">{errors.new_password}</p>}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">Confirm password</label>
                    <input
                      type="password"
                      name="confirm_password"
                      value={form.confirm_password}
                      onChange={handleChange}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
                    />
                    {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password}</p>}
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <p className="text-sm font-medium text-gray-700">Password requirements</p>
                    <div className="mt-3 space-y-2 text-sm text-gray-600">
                      {passwordChecklist.map((rule) => (
                        <div key={rule.label} className={rule.ok ? "text-green-700" : "text-gray-500"}>
                          {rule.ok ? "Pass" : "Pending"} - {rule.label}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <Button type="button" variant="secondary" onClick={handleClose}>
                      Cancel
                    </Button>
                    <Button type="submit" isLoading={changePassword.isPending}>
                      Update Password
                    </Button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}