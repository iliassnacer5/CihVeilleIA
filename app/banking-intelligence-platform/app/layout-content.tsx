'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  FileText,
  Search,
  MessageSquare,
  AlertCircle,
  BarChart3,
  Settings,
  Globe,
  ChevronDown,
  Menu,
  X,
  User,
  LogOut,
  Shield,
  Bell,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface NavItem {
  label: string
  icon: React.ReactNode
  href: string
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: <LayoutDashboard size={20} />, href: '/' },
  {
    label: 'Sources Management',
    icon: <Globe size={20} />,
    href: '/sources',
  },
  {
    label: 'Collected Documents',
    icon: <FileText size={20} />,
    href: '/documents',
  },
  { label: 'Semantic Search', icon: <Search size={20} />, href: '/search' },
  { label: 'AI Chatbot', icon: <MessageSquare size={20} />, href: '/chatbot' },
  {
    label: 'Alerts & Monitoring',
    icon: <AlertCircle size={20} />,
    href: '/alerts',
  },
  {
    label: 'Analytics & KPIs',
    icon: <BarChart3 size={20} />,
    href: '/analytics',
  },
  {
    label: 'Audit & Compliance',
    icon: <Shield size={20} />,
    href: '/audit',
  },
  { label: 'Settings', icon: <Settings size={20} />, href: '/settings' },
]

export function LayoutContent({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const pathname = usePathname()

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-sidebar text-sidebar-foreground transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } md:static md:translate-x-0 md:w-64`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-sidebar-border">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-sidebar-accent rounded-lg flex items-center justify-center">
                <Globe size={16} className="text-sidebar-accent-foreground" />
              </div>
              <span className="font-semibold text-lg hidden sm:inline">CIH</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                    }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-sidebar-border">
            <button className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-sidebar-accent rounded-full flex items-center justify-center">
                  <User size={16} className="text-sidebar-accent-foreground" />
                </div>
                <div className="text-left hidden sm:block">
                  <div className="text-sm font-medium">John Doe</div>
                  <div className="text-xs opacity-70">Admin</div>
                </div>
              </div>
              <ChevronDown size={16} className="hidden sm:block" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="bg-card border-b border-border h-16 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden p-2 hover:bg-secondary rounded-lg transition-colors"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-lg font-semibold text-foreground">
              AI Intelligence & Web Monitoring Platform
            </h1>
          </div>

          {/* Top Right Actions */}
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground">
              <AlertCircle size={20} />
            </button>
            <button className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground">
              <User size={20} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 md:p-8">{children}</div>
        </main>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
