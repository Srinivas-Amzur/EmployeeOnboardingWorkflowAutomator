import React, { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { ArrowDownUp, CheckCircle2, ChevronDown, ChevronRight, ChevronUp, Circle, Plus, Search, SlidersHorizontal, X } from "lucide-react"
import { Button } from "../components/common/Button"
import { EmptyState } from "../components/common/EmptyState"
import { ProgressBar } from "../components/common/ProgressBar"
import { Skeleton } from "../components/common/Skeleton"
import { StatusBadge } from "../components/common/StatusBadge"
import {
  useEmployees,
  useWorkflowEvents,
  useWorkflows,
  useWorkflowSnapshot,
  useWorkflowTasks,
} from "../hooks"
import { formatRelativeTime } from "../lib/time"

const WORKFLOW_STATES = ["initiated", "hr_review", "provisioning", "meetings_scheduled", "documents_shared", "completed"]

const WORKFLOW_STAGE_LABELS: Record<string, string> = {
  initiated: "Initiated",
  hr_review: "HR Review",
  provisioning: "Provisioning",
  meetings_scheduled: "Meeting Scheduled",
  documents_shared: "Documents Shared",
  completed: "Completed",
}

export const OnboardingListPage: React.FC = () => {
  const [skip, setSkip] = useState(0)
  const [search, setSearch] = useState("")
  const [stateFilter, setStateFilter] = useState("all")
  const [departmentFilter, setDepartmentFilter] = useState("all")
  const [dateFilter, setDateFilter] = useState("all")
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<"id" | "employee" | "department" | "stage" | "progress" | "created">("created")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")
  const limit = 20

  const { data: workflows = [], isLoading, error } = useWorkflows({ skip, limit })
  const { data: employees = [] } = useEmployees(0, 500)

  const selectedWorkflow = useMemo(
    () => workflows.find((workflow) => workflow.id === selectedWorkflowId) ?? null,
    [workflows, selectedWorkflowId],
  )

  const { data: selectedTasks = [] } = useWorkflowTasks(selectedWorkflowId)
  const { data: selectedSnapshot } = useWorkflowSnapshot(selectedWorkflowId)
  const { data: selectedEvents = [] } = useWorkflowEvents(selectedWorkflowId)

  const employeeMap = useMemo(() => {
    const map = new Map<string, { department: string; name: string; company_email: string | null }>()
    for (const employee of employees) {
      map.set(employee.id, {
        department: employee.department,
        name: `${employee.first_name} ${employee.last_name}`,
        company_email: employee.company_email ?? null,
      })
    }
    return map
  }, [employees])

  const departments = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.department))).sort((a, b) => a.localeCompare(b)),
    [employees],
  )

  const filteredWorkflows = useMemo(() => {
    const now = Date.now()
    return workflows.filter((workflow) => {
      const employee = employeeMap.get(workflow.employee_id)
      const startedTs = new Date(workflow.started_at).getTime()
      const ageHours = (now - startedTs) / (1000 * 60 * 60)
      const matchesSearch =
        search.trim().length === 0 ||
        workflow.id.toLowerCase().includes(search.toLowerCase()) ||
        workflow.employee_id.toLowerCase().includes(search.toLowerCase()) ||
        (employee?.name ?? "").toLowerCase().includes(search.toLowerCase())
      const matchesState = stateFilter === "all" || workflow.current_state === stateFilter
      const matchesDepartment = departmentFilter === "all" || employee?.department === departmentFilter
      const matchesDate =
        dateFilter === "all" ||
        (dateFilter === "today" && ageHours <= 24) ||
        (dateFilter === "week" && ageHours <= 24 * 7) ||
        (dateFilter === "month" && ageHours <= 24 * 30)
      return matchesSearch && matchesState && matchesDepartment && matchesDate
    })
  }, [dateFilter, departmentFilter, employeeMap, search, stateFilter, workflows])

  const taskStats = useMemo(() => {
    const total = selectedTasks.length
    const completed = selectedTasks.filter((task) => task.status === "completed").length
    const overdue = selectedTasks.filter((task) => {
      if (!task.due_date || task.status === "completed") return false
      return new Date(task.due_date).getTime() < Date.now()
    }).length
    const blocked = selectedTasks.filter((task) => task.status === "blocked").length
    return { total, completed, overdue, blocked }
  }, [selectedTasks])

  const activeFilters = [search, stateFilter, departmentFilter, dateFilter].filter((value, index) => {
    if (index === 0) return value.trim().length > 0
    return value !== "all"
  }).length

  const clearFilters = () => {
    setSearch("")
    setStateFilter("all")
    setDepartmentFilter("all")
    setDateFilter("all")
  }

  const sortedWorkflows = useMemo(() => {
    const rows = [...filteredWorkflows]
    rows.sort((a, b) => {
      const employeeA = employeeMap.get(a.employee_id)?.name ?? ""
      const employeeB = employeeMap.get(b.employee_id)?.name ?? ""
      const departmentA = employeeMap.get(a.employee_id)?.department ?? ""
      const departmentB = employeeMap.get(b.employee_id)?.department ?? ""

      let compare = 0
      if (sortBy === "id") compare = a.id.localeCompare(b.id)
      if (sortBy === "employee") compare = employeeA.localeCompare(employeeB)
      if (sortBy === "department") compare = departmentA.localeCompare(departmentB)
      if (sortBy === "stage") compare = a.current_state.localeCompare(b.current_state)
      if (sortBy === "progress") compare = a.completion_percentage - b.completion_percentage
      if (sortBy === "created") compare = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()

      return sortDir === "asc" ? compare : -compare
    })
    return rows
  }, [employeeMap, filteredWorkflows, sortBy, sortDir])

  const toggleSort = (column: "id" | "employee" | "department" | "stage" | "progress" | "created") => {
    if (sortBy === column) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"))
      return
    }
    setSortBy(column)
    setSortDir("asc")
  }

  const SortIcon = ({ col }: { col: typeof sortBy }) => {
    if (sortBy !== col) return <ArrowDownUp className="ml-1 h-3 w-3 text-slate-300 dark:text-slate-600" />
    return sortDir === "asc"
      ? <ChevronUp className="ml-1 h-3 w-3 text-violet-500" />
      : <ChevronDown className="ml-1 h-3 w-3 text-violet-500" />
  }

  return (
    <section className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Onboarding Workflows</h1>
          <p className="page-subtitle">
            {filteredWorkflows.length} of {workflows.length} workflows
            {activeFilters > 0 ? ` · ${activeFilters} filter${activeFilters > 1 ? "s" : ""} active` : ""}
          </p>
        </div>
        <Link to="/employees/new">
          <Button size="sm">
            <Plus className="h-3.5 w-3.5" />
            New Employee
          </Button>
        </Link>
      </div>

      {/* Filter bar */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by workflow ID, employee name..."
            className="surface-input pl-8"
            aria-label="Search workflows"
          />
        </div>
        <div className="flex gap-2">
          <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} className="surface-select w-36" aria-label="Filter by state">
            <option value="all">All states</option>
            {WORKFLOW_STATES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
          </select>
          <select value={departmentFilter} onChange={(e) => setDepartmentFilter(e.target.value)} className="surface-select w-36" aria-label="Filter by department">
            <option value="all">All departments</option>
            {departments.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
          <select value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="surface-select w-32" aria-label="Filter by date">
            <option value="all">Any time</option>
            <option value="today">Today</option>
            <option value="week">This week</option>
            <option value="month">This month</option>
          </select>
          {activeFilters > 0 && (
            <Button size="sm" variant="secondary" onClick={clearFilters}>
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/30 dark:text-rose-200">
          Error loading workflows - please refresh.
        </div>
      )}

      {/* Data table */}
      <div className="surface-card overflow-hidden">
        {isLoading ? (
          <div className="space-y-px p-3">
            {["l1","l2","l3","l4","l5"].map((k) => <Skeleton key={k} className="h-10 rounded-lg" />)}
          </div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No matching workflows"
              description="Adjust filters or create a new employee to start a workflow."
              action={<Button variant="secondary" size="sm" onClick={clearFilters}>Clear filters</Button>}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="cursor-pointer pl-5 select-none" onClick={() => toggleSort("id")}>
                    <span className="inline-flex items-center">Workflow <SortIcon col="id" /></span>
                  </th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort("employee")}>
                    <span className="inline-flex items-center">Employee <SortIcon col="employee" /></span>
                  </th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort("department")}>
                    <span className="inline-flex items-center">Department <SortIcon col="department" /></span>
                  </th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort("stage")}>
                    <span className="inline-flex items-center">Stage <SortIcon col="stage" /></span>
                  </th>
                  <th className="w-40 cursor-pointer select-none" onClick={() => toggleSort("progress")}>
                    <span className="inline-flex items-center">Progress <SortIcon col="progress" /></span>
                  </th>
                  <th className="cursor-pointer select-none" onClick={() => toggleSort("created")}>
                    <span className="inline-flex items-center">Updated <SortIcon col="created" /></span>
                  </th>
                  <th className="w-12 pr-4"></th>
                </tr>
              </thead>
              <tbody>
                {sortedWorkflows.map((wf) => {
                  const emp = employeeMap.get(wf.employee_id)
                  const isSelected = wf.id === selectedWorkflowId
                  return (
                    <tr
                      key={wf.id}
                      className={`cursor-pointer ${isSelected ? "!bg-violet-50 dark:!bg-blue-900/20" : ""}`}
                      onClick={() => setSelectedWorkflowId(wf.id === selectedWorkflowId ? null : wf.id)}
                    >
                      <td className="pl-5">
                        <p className="font-mono text-xs font-semibold text-slate-700 dark:text-slate-300">
                          #{wf.id.substring(0, 8)}
                        </p>
                      </td>
                      <td className="font-medium text-slate-900 dark:text-slate-100">{emp?.name ?? "-"}</td>
                      <td className="text-sm text-slate-500 dark:text-slate-400">{emp?.department ?? "-"}</td>
                      <td><StatusBadge value={wf.current_state} /></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                            <div className="h-full rounded-full bg-violet-500 transition-all" style={{ width: `${wf.completion_percentage}%` }} />
                          </div>
                          <span className="w-8 text-right text-xs tabular-nums text-slate-500">
                            {Math.round(wf.completion_percentage)}%
                          </span>
                        </div>
                      </td>
                      <td className="text-xs text-slate-400">{formatRelativeTime(wf.updated_at)}</td>
                      <td className="pr-4">
                        <Link
                          to={`/onboarding/${wf.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="flex items-center justify-center rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                          aria-label="Open workflow"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && workflows.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-2.5 dark:border-slate-800">
            <p className="text-[12px] text-slate-500">Showing {skip + 1}-{Math.min(skip + limit, skip + sortedWorkflows.length)} of {skip + sortedWorkflows.length}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setSkip(Math.max(0, skip - limit))} disabled={skip === 0}>Prev</Button>
              <Button size="sm" variant="outline" onClick={() => setSkip(skip + limit)}>Next</Button>
            </div>
          </div>
        )}
      </div>

      {/* Detail drawer */}
      {selectedWorkflow && (
        <div className="fixed inset-0 z-50 flex">
          <button className="h-full w-full bg-slate-950/30" onClick={() => setSelectedWorkflowId(null)} aria-label="Close" />
          <aside
            className="ml-auto h-full w-full max-w-[480px] overflow-y-auto shadow-elevation-3"
            style={{
              borderLeft: "1px solid var(--surface-border)",
              backgroundColor: "var(--surface-base)",
            }}
          >
            <div
              className="sticky top-0 z-10 flex items-center justify-between border-b px-4 py-3"
              style={{ borderColor: "var(--surface-border)", backgroundColor: "color-mix(in srgb, var(--surface-base) 95%, transparent)" }}
            >
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Workflow #{selectedWorkflow.id.substring(0, 8)}</p>
                <p className="text-xs text-slate-500">{employeeMap.get(selectedWorkflow.employee_id)?.name}</p>
                {employeeMap.get(selectedWorkflow.employee_id)?.company_email && (
                  <p className="text-xs font-medium text-violet-600 dark:text-violet-400">{employeeMap.get(selectedWorkflow.employee_id)?.company_email}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Link to={`/onboarding/${selectedWorkflow.id}`}><Button size="sm">Open</Button></Link>
                <button onClick={() => setSelectedWorkflowId(null)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Close"><X className="h-4 w-4" /></button>
              </div>
            </div>

            <div className="space-y-4 p-4">
              {/* Summary row */}
              <div className="flex items-center justify-between gap-3">
                <StatusBadge value={selectedWorkflow.current_state} />
                <ProgressBar value={selectedWorkflow.completion_percentage} className="flex-1" />
                <span className="text-xs tabular-nums text-slate-500">{Math.round(selectedWorkflow.completion_percentage)}%</span>
              </div>

              {/* Task stats */}
              <div>
                <p className="section-label mb-2">Tasks</p>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label: "Total", value: taskStats.total, cls: "bg-slate-50 dark:bg-slate-900/70" },
                    { label: "Done", value: taskStats.completed, cls: "bg-emerald-50 dark:bg-emerald-500/10" },
                    { label: "Overdue", value: taskStats.overdue, cls: "bg-amber-50 dark:bg-amber-500/10" },
                    { label: "Blocked", value: taskStats.blocked, cls: "bg-rose-50 dark:bg-rose-500/10" },
                  ].map((t) => (
                    <div key={t.label} className={`rounded-xl border border-slate-200/70 p-3 text-center dark:border-slate-700 ${t.cls}`}>
                      <p className="text-lg font-bold tabular-nums text-slate-900 dark:text-slate-100">{t.value}</p>
                      <p className="section-label mt-0.5">{t.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Lifecycle */}
              <div>
                <p className="section-label mb-2">Lifecycle</p>
                <div className="space-y-1">
                  {WORKFLOW_STATES.map((state, index) => {
                    const currentIndex = WORKFLOW_STATES.indexOf(selectedWorkflow.current_state)
                    const isComplete = index < currentIndex
                    const isCurrent = index === currentIndex
                    return (
                      <div key={state} className={`flex items-center gap-2.5 rounded-xl border px-3 py-2 ${isCurrent ? "border-violet-200 bg-violet-50 dark:border-blue-700 dark:bg-blue-900/20" : "border-slate-100 dark:border-slate-800"}`}>
                        <span className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${isComplete ? "bg-emerald-500 text-white" : isCurrent ? "bg-slate-900 text-white dark:bg-sky-500 dark:text-slate-950" : "bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-300"}`}>
                          {isComplete ? <CheckCircle2 className="h-3 w-3" /> : <Circle className="h-2.5 w-2.5" />}
                        </span>
                        <p className={`text-sm ${isCurrent ? "font-semibold text-slate-900 dark:text-slate-100" : "text-slate-500 dark:text-slate-400"}`}>{WORKFLOW_STAGE_LABELS[state]}</p>
                        {isCurrent && <span className="ml-auto text-xs font-semibold text-blue-600 dark:text-sky-400">Current</span>}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Events */}
              <div>
                <p className="section-label mb-2">Recent Events</p>
                {selectedEvents.length === 0 ? (
                  <p className="text-xs text-slate-400">No events yet.</p>
                ) : (
                  <div className="space-y-1.5">
                    {selectedEvents.slice(0, 6).map((event) => (
                      <div key={event.id} className="rounded-xl border border-slate-100 bg-slate-50/80 px-3 py-2 dark:border-slate-800 dark:bg-slate-900/60">
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">{event.event_type.replaceAll("_", " ")}</p>
                        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{event.message}</p>
                        <p className="mt-0.5 text-xs text-slate-400">{formatRelativeTime(event.created_at)}</p>
                      </div>
                    ))}
                  </div>
                )}
                {selectedSnapshot && (
                  <p className="mt-2 text-xs text-slate-400">Snapshot synced {formatRelativeTime(selectedSnapshot.synced_at)}</p>
                )}
              </div>
            </div>
          </aside>
        </div>
      )}
    </section>
  )
}

