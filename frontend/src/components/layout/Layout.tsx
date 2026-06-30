import React from "react"
import { motion } from "framer-motion"
import { EnterpriseSidebar } from "./EnterpriseSidebar"
import { EnterpriseTopbar } from "./EnterpriseTopbar"

interface LayoutProps {
  children: React.ReactNode
}

const pageVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.22, 1, 0.36, 1] } },
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false)

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--surface-page)" }}>
      <EnterpriseSidebar
        collapsed={false}
        mobileOpen={mobileSidebarOpen}
        onToggleCollapse={() => {}}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <div className="min-h-screen lg:ml-[88px]">
        <EnterpriseTopbar onOpenSidebar={() => setMobileSidebarOpen(true)} />

        <main className="px-4 py-5 sm:px-6 sm:py-6">
          <div className="mx-auto max-w-[1600px]">
            <motion.div variants={pageVariants} initial="hidden" animate="visible">
              {children}
            </motion.div>
          </div>
        </main>
      </div>
    </div>
  )
}
