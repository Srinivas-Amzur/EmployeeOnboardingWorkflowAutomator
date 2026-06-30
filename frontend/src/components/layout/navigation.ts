import {
  BarChart3,
  Bell,
  BrainCircuit,
  CircleUser,
  GitBranch,
  LayoutDashboard,
  ScrollText,
  UserCog,
  UserPlus,
  Users,
  PlusCircle,
  type LucideIcon,
} from "lucide-react"

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export const SIDEBAR_SECTIONS: NavSection[] = [
  {
    title: "Core",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/onboarding", label: "Workflows", icon: GitBranch },
      { to: "/employees/new", label: "New Employee", icon: UserPlus },
    ],
  },
  {
    title: "Workspace",
    items: [
      { to: "/portal", label: "Employee Portal", icon: UserCog },
      { to: "/notifications", label: "Notifications", icon: Bell },
      { to: "/assistant", label: "AI Assistant", icon: BrainCircuit },
    ],
  },
  {
    title: "Insights",
    items: [
      { to: "/analytics", label: "Analytics", icon: BarChart3 },
      { to: "/audit-logs", label: "Audit Logs", icon: ScrollText },
    ],
  },
  {
    title: "Account",
    items: [
      { to: "/profile", label: "Profile", icon: CircleUser },
    ],
  },
]

export const QUICK_ACTION_LINK = { to: "/employees/new", label: "New Employee", icon: PlusCircle }

// Unused but kept for reference
export const _ALL_USERS_ICON = Users

export const isActivePath = (pathname: string, to: string): boolean => pathname === to || pathname.startsWith(`${to}/`)
