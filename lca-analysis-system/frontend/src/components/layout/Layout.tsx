import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Leaf, Upload, BarChart3, FileText } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { path: '/', label: 'Upload', icon: Upload },
  { path: '/processing', label: 'Processing', icon: BarChart3 },
  { path: '/report', label: 'Report', icon: FileText },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="flex h-screen bg-bg-primary text-text-primary overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-bg-secondary border-r border-white/5 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-green/10 flex items-center justify-center">
              <Leaf className="w-5 h-5 text-accent-green" />
            </div>
            <div>
              <h1 className="font-heading text-lg font-semibold text-text-primary">
                LCA Analyst
              </h1>
              <p className="text-xs text-text-muted font-mono">Multi-Agent System</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                  active
                    ? 'bg-accent-green/10 text-accent-green'
                    : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-body">{item.label}</span>
                {active && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-green"
                  />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/5">
          <p className="text-xs text-text-muted font-mono text-center">
            v1.0.0 · Multi-Agent LCA
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">{children}</div>
      </main>
    </div>
  )
}
