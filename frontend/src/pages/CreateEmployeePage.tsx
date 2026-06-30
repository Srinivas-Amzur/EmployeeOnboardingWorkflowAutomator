import React, { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  Circle,
  ClipboardList,
  Mail,
  Settings2,
  UserCircle2,
  UserPlus,
} from "lucide-react"
import { useCreateEmployee } from "../hooks"
import { Button } from "../components/common/Button"

// ── Types (unchanged) ────────────────────────────────────────────────────────
interface FormState {
  first_name: string
  last_name: string
  email: string
  department: string
  designation: string
  joining_date: string
  manager_id: string
}

const DEPARTMENTS = [
  "Engineering", "Product", "Design", "Marketing", "Sales",
  "HR", "Finance", "Operations", "Legal", "Customer Success",
]

const initialForm: FormState = {
  first_name: "", last_name: "", email: "",
  department: "", designation: "", joining_date: "", manager_id: "",
}

const STEPS = ["Profile", "Role details", "Start date"]

const WORKFLOW_STAGES = [
  "Employee Created", "HR Review", "IT Provisioning", "Meetings Scheduled", "Completed",
]

// ── Shared input class ───────────────────────────────────────────────────────
const INPUT_BASE =
  "h-[46px] w-full rounded-[10px] border border-slate-300 bg-white px-[14px] text-[15px] text-slate-900 placeholder:text-slate-400 outline-none transition-all duration-150 " +
  "hover:border-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/15"

const INPUT_ERROR =
  "border-rose-400 hover:border-rose-400 focus:border-rose-500 focus:ring-rose-500/15"

const ICON_CLASS =
  "pointer-events-none absolute left-[14px] top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"

// ── Helper ───────────────────────────────────────────────────────────────────
function formatDate(iso: string) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })
}

// ── Page ─────────────────────────────────────────────────────────────────────
export const CreateEmployeePage: React.FC = () => {
  const navigate = useNavigate()
  const createEmployee = useCreateEmployee()

  // ── State (unchanged) ──────────────────────────────────────────────────────
  const [form, setForm] = useState<FormState>(initialForm)
  const [errors, setErrors] = useState<Partial<FormState>>({})

  // ── Validation (unchanged) ─────────────────────────────────────────────────
  const validate = (): boolean => {
    const newErrors: Partial<FormState> = {}
    if (!form.first_name.trim()) newErrors.first_name = "Required"
    if (!form.last_name.trim()) newErrors.last_name = "Required"
    if (!form.email.trim()) {
      newErrors.email = "Required"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = "Invalid email"
    }
    if (!form.department) newErrors.department = "Required"
    if (!form.designation.trim()) newErrors.designation = "Required"
    if (!form.joining_date) newErrors.joining_date = "Required"
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // ── Handlers (unchanged) ───────────────────────────────────────────────────
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" && "checked" in e.target ? e.target.checked : value,
    }))
    if (errors[name as keyof FormState]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const payload = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      department: form.department,
      designation: form.designation.trim(),
      joining_date: form.joining_date,
      manager_id: form.manager_id || null,
    }

    try {
      await createEmployee.mutateAsync(payload)
      navigate("/onboarding")
    } catch (err) {
      console.error("Create employee request failed", err)
    }
  }

  // ── Derived (unchanged) ────────────────────────────────────────────────────
  const isSubmitting = createEmployee.isPending
  const serverError = createEmployee.error?.message

  const previewName = [form.first_name.trim(), form.last_name.trim()].filter(Boolean).join(" ") || "New Employee"

  const previewCompanyEmail = useMemo(() => {
    const fn = form.first_name.trim().toLowerCase().replace(/[^a-z0-9]/g, ".")
    const ln = form.last_name.trim().toLowerCase().replace(/[^a-z0-9]/g, ".")
    if (!fn || !ln) return ""
    return `${fn}.${ln}@company.local`
  }, [form.first_name, form.last_name])

  const previewCompletion = useMemo(() => {
    const filled = [form.first_name, form.last_name, form.email, form.department, form.designation, form.joining_date]
      .filter((v) => v.trim().length > 0).length
    return Math.round((filled / 6) * 100)
  }, [form])

  const stepProgress = useMemo(() => {
    const profileDone = Boolean(form.first_name.trim() && form.last_name.trim() && form.email.trim())
    const roleDone    = Boolean(form.department.trim() && form.designation.trim())
    const startDone   = Boolean(form.joining_date)
    return [profileDone, roleDone, startDone]
  }, [form.department, form.designation, form.email, form.first_name, form.joining_date, form.last_name])

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <section className="animate-fade-in space-y-8" style={{ background: "#F8FAFC" }}>

      {/* ── Page header ── */}
      <div className="space-y-5">

        {/* Badge + title */}
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-700">
            Employee Intake
          </span>
          <h1 className="mt-3 text-slate-900 leading-tight" style={{ fontSize: "34px", fontWeight: 700 }}>
            Create Employee
          </h1>
          <p className="mt-2 max-w-xl text-[14px] leading-relaxed text-slate-500">
            Add a new employee profile and trigger onboarding automation from this guided form.
          </p>
        </div>

        {/* ── Stepper ── */}
        <div className="flex flex-wrap items-center gap-x-0 gap-y-3">
          {STEPS.map((step, i) => {
            const done    = stepProgress[i]
            const current = !done && stepProgress.slice(0, i).every(Boolean)
            return (
              <React.Fragment key={step}>
                <div className="flex items-center gap-2.5">
                  {/* Circle */}
                  <span className={[
                    "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold transition-all duration-200",
                    done    ? "bg-emerald-500 text-white shadow-sm"
                    : current ? "bg-violet-600 text-white shadow-sm shadow-violet-200"
                    : "border-2 border-slate-300 bg-white text-slate-400",
                  ].join(" ")}>
                    {done ? <CheckCircle2 className="h-[18px] w-[18px]" /> : <span>{i + 1}</span>}
                  </span>
                  {/* Label */}
                  <span className={[
                    "text-[14px] font-semibold whitespace-nowrap",
                    done ? "text-emerald-600" : current ? "text-violet-600" : "text-slate-400",
                  ].join(" ")}>
                    {step}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={[
                    "mx-4 h-px w-12 flex-shrink-0 transition-colors duration-300",
                    done ? "bg-emerald-300" : "bg-slate-200",
                  ].join(" ")} />
                )}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {/* ── Server error ── */}
      {serverError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/30 dark:text-rose-200">
          {serverError}
        </div>
      )}

      {/* ── Main grid ── */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.6fr)_380px]">

        {/* ── Left: form card ── */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm" style={{ padding: "28px" }}>
          <form onSubmit={handleSubmit} className="space-y-8">

            {/* ── Profile section ── */}
            <div>
              <h2 className="text-slate-900" style={{ fontSize: "22px", fontWeight: 600 }}>Profile</h2>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-500">
                Identity and contact information used by the onboarding workflow.
              </p>

              <div className="mt-5 grid gap-[18px] sm:grid-cols-2">
                {/* First name */}
                <div>
                  <label htmlFor="first_name" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    First name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="first_name"
                    name="first_name"
                    value={form.first_name}
                    onChange={handleChange}
                    aria-invalid={Boolean(errors.first_name)}
                    className={`${INPUT_BASE} ${errors.first_name ? INPUT_ERROR : ""}`}
                    placeholder="John"
                  />
                  {errors.first_name && <p className="mt-1.5 text-xs text-rose-600">{errors.first_name}</p>}
                </div>

                {/* Last name */}
                <div>
                  <label htmlFor="last_name" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    Last name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="last_name"
                    name="last_name"
                    value={form.last_name}
                    onChange={handleChange}
                    aria-invalid={Boolean(errors.last_name)}
                    className={`${INPUT_BASE} ${errors.last_name ? INPUT_ERROR : ""}`}
                    placeholder="Doe"
                  />
                  {errors.last_name && <p className="mt-1.5 text-xs text-rose-600">{errors.last_name}</p>}
                </div>

                {/* Email — full width */}
                <div className="sm:col-span-2">
                  <label htmlFor="email" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    Work email <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className={ICON_CLASS} />
                    <input
                      id="email"
                      type="email"
                      name="email"
                      value={form.email}
                      onChange={handleChange}
                      aria-invalid={Boolean(errors.email)}
                      className={`${INPUT_BASE} pl-[44px] ${errors.email ? INPUT_ERROR : ""}`}
                      placeholder="john.doe@company.com"
                    />
                  </div>
                  {errors.email && <p className="mt-1.5 text-xs text-rose-600">{errors.email}</p>}
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="h-px bg-slate-100" />

            {/* ── Role details section ── */}
            <div>
              <h2 className="text-slate-900" style={{ fontSize: "22px", fontWeight: 600 }}>Role details</h2>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-500">
                Job information used to route onboarding tasks and provisioning.
              </p>

              <div className="mt-5 space-y-[18px]">
                {/* Department */}
                <div>
                  <label htmlFor="department" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    Department <span className="text-rose-500">*</span>
                  </label>
                  <select
                    id="department"
                    name="department"
                    value={form.department}
                    onChange={handleChange}
                    aria-invalid={Boolean(errors.department)}
                    className={[
                      "h-[46px] w-full appearance-none rounded-[10px] border border-slate-300 bg-white pl-[14px] pr-10 text-[15px] text-slate-900 outline-none transition-all duration-150",
                      "hover:border-slate-400 focus:border-violet-500 focus:ring-2 focus:ring-violet-500/15",
                      errors.department ? "border-rose-400 hover:border-rose-400 focus:border-rose-500 focus:ring-rose-500/15" : "",
                    ].join(" ")}
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                  {errors.department && <p className="mt-1.5 text-xs text-rose-600">{errors.department}</p>}
                </div>

                {/* Designation */}
                <div>
                  <label htmlFor="designation" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    Designation / job title <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <BriefcaseBusiness className={ICON_CLASS} />
                    <input
                      id="designation"
                      name="designation"
                      value={form.designation}
                      onChange={handleChange}
                      aria-invalid={Boolean(errors.designation)}
                      className={`${INPUT_BASE} pl-[44px] ${errors.designation ? INPUT_ERROR : ""}`}
                      placeholder="Senior Software Engineer"
                    />
                  </div>
                  {errors.designation && <p className="mt-1.5 text-xs text-rose-600">{errors.designation}</p>}
                </div>

                {/* Manager ID */}
                <div>
                  <label htmlFor="manager_id" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                    Manager ID
                    <span className="ml-2 text-[12px] font-normal text-slate-400">optional</span>
                  </label>
                  <div className="relative">
                    <UserCircle2 className={ICON_CLASS} />
                    <input
                      id="manager_id"
                      name="manager_id"
                      value={form.manager_id}
                      onChange={handleChange}
                      className={`${INPUT_BASE} pl-[44px]`}
                      placeholder="e.g. usr_abc123"
                    />
                  </div>
                  <p className="mt-1.5 text-[13px] text-slate-400">
                    Optional manager reference for reporting and approvals.
                  </p>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="h-px bg-slate-100" />

            {/* ── Start date section ── */}
            <div>
              <h2 className="text-slate-900" style={{ fontSize: "22px", fontWeight: 600 }}>Start date</h2>
              <p className="mt-2 text-[14px] leading-relaxed text-slate-500">
                The onboarding workflow starts automatically from this date.
              </p>

              <div className="mt-5 max-w-sm">
                <label htmlFor="joining_date" className="mb-1.5 block text-[15px] font-medium text-slate-700">
                  Joining date <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <CalendarDays className={ICON_CLASS} />
                  <input
                    id="joining_date"
                    type="date"
                    name="joining_date"
                    value={form.joining_date}
                    onChange={handleChange}
                    aria-invalid={Boolean(errors.joining_date)}
                    className={`${INPUT_BASE} pl-[44px] ${errors.joining_date ? INPUT_ERROR : ""}`}
                  />
                </div>
                {errors.joining_date && <p className="mt-1.5 text-xs text-rose-600">{errors.joining_date}</p>}
              </div>

              {/* Automation notice */}
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-violet-200 bg-violet-50/70 px-4 py-3">
                <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-600 text-white text-[10px] font-bold">✓</span>
                <p className="text-[13px] leading-relaxed text-violet-900">
                  <span className="font-semibold">Workflow automation enabled</span> — creating this employee will automatically trigger a full onboarding workflow.
                </p>
              </div>
            </div>

            {/* ── Submit row ── */}
            <div className="flex flex-col gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center">
              <Button
                type="submit"
                disabled={isSubmitting}
                isLoading={isSubmitting}
                className="h-[44px] rounded-[10px] px-6 text-[15px] font-semibold"
              >
                {isSubmitting ? "Creating…" : "Create Employee"}
              </Button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="h-[44px] rounded-[10px] border border-slate-300 bg-white px-6 text-[15px] font-semibold text-slate-700 transition-colors hover:bg-slate-50 hover:border-slate-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* ── Right column ── */}
        <div className="space-y-5">

          {/* ── Live Preview card ── */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm" style={{ padding: "24px" }}>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Live Preview</p>

            {/* Avatar + name */}
            <div className="mt-4 flex items-center gap-3">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-700 text-[15px] font-bold">
                {form.first_name && form.last_name
                  ? `${form.first_name[0]}${form.last_name[0]}`.toUpperCase()
                  : <UserPlus className="h-5 w-5" />}
              </div>
              <div>
                <p className="text-[18px] font-semibold text-slate-900 leading-tight">{previewName}</p>
                <p className="mt-0.5 text-[13px] text-slate-500">{form.designation || "Role not set"}</p>
              </div>
            </div>

            {/* Fields */}
            <div className="mt-5 space-y-2.5">
              {[
                { icon: <Mail className="h-3.5 w-3.5" />, label: "Work Email",      value: form.email       },
                { icon: <Mail className="h-3.5 w-3.5 text-violet-500" />, label: "Company Email", value: previewCompanyEmail },
                { icon: <BriefcaseBusiness className="h-3.5 w-3.5" />, label: "Department", value: form.department },
                { icon: <CalendarDays className="h-3.5 w-3.5" />, label: "Start date",  value: formatDate(form.joining_date) ?? "" },
              ].map(({ icon, label, value }) => (
                <div key={label} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2.5">
                  <div className="flex items-center gap-2 text-slate-400">
                    {icon}
                    <span className="text-[12px] font-medium text-slate-500">{label}</span>
                  </div>
                  <span className="max-w-[52%] truncate text-right text-[13px] font-semibold text-slate-900">
                    {value || <span className="font-normal text-slate-300">—</span>}
                  </span>
                </div>
              ))}
            </div>

            {/* Progress bar */}
            <div className="mt-5">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-medium text-slate-500">Profile completion</span>
                <span className="text-[12px] font-bold text-violet-600">{previewCompletion}%</span>
              </div>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-violet-500 transition-all duration-500"
                  style={{ width: `${previewCompletion}%` }}
                />
              </div>
            </div>

            {/* Workflow stages */}
            <div className="mt-5">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">Workflow Progress</p>
              <div className="space-y-2">
                {WORKFLOW_STAGES.map((stage, i) => {
                  const done = previewCompletion === 100 && i === 0
                  return (
                    <div key={stage} className="flex items-center gap-2.5">
                      <span className={[
                        "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full",
                        done
                          ? "bg-emerald-500 text-white"
                          : "border-2 border-slate-200",
                      ].join(" ")}>
                        {done
                          ? <CheckCircle2 className="h-3 w-3" />
                          : <Circle className="h-2.5 w-2.5 text-slate-300" />}
                      </span>
                      <span className={[
                        "text-[13px]",
                        done ? "font-semibold text-emerald-700" : i === 0 ? "font-medium text-slate-700" : "text-slate-400",
                      ].join(" ")}>
                        {stage}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* ── Guidance card ── */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm" style={{ padding: "24px" }}>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">What Happens Next</p>
            <h3 className="mt-2 text-[16px] font-semibold text-slate-900">After you submit</h3>

            <div className="mt-4 space-y-3">
              {[
                {
                  icon: <CheckCircle2 className="h-4 w-4 text-emerald-600" />,
                  bg:   "bg-emerald-50 border-emerald-100",
                  text: "Employee record is created and saved to your org directory.",
                },
                {
                  icon: <Mail className="h-4 w-4 text-violet-600" />,
                  bg:   "bg-violet-50 border-violet-100",
                  text: "A company email (firstname.lastname@company.local) is generated and provisioned automatically.",
                },
                {
                  icon: <Settings2 className="h-4 w-4 text-sky-600" />,
                  bg:   "bg-sky-50 border-sky-100",
                  text: "Onboarding workflow starts automatically and a welcome email is sent to the employee, manager, and HR.",
                },
                {
                  icon: <ClipboardList className="h-4 w-4 text-amber-600" />,
                  bg:   "bg-amber-50 border-amber-100",
                  text: "Verify the live preview fields before submitting to avoid re-work.",
                },
              ].map(({ icon, bg, text }, i) => (
                <div key={i} className={`flex items-start gap-3 rounded-xl border px-4 py-3 ${bg}`}>
                  <span className="mt-0.5 flex-shrink-0">{icon}</span>
                  <p className="text-[13px] leading-relaxed text-slate-700">{text}</p>
                </div>
              ))}
            </div>

            <div className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-[12px] leading-relaxed text-slate-500">
              Tasks, meetings, and notifications will appear in the workflow detail and dashboard views once the workflow is triggered.
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
