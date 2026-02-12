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

import { useAuth } from './context/AuthContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function LayoutContent({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const pathname = usePathname()
  const { user, logout, isLoading } = useAuth()

  // Hide sidebar and header on login page
  const isLoginPage = pathname === '/login'

  if (isLoginPage) {
    return <main>{children}</main>
  }

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Globe className="w-12 h-12 text-primary animate-pulse" />
          <p className="text-muted-foreground font-medium">Chargement de la plateforme...</p>
        </div>
      </div>
    )
  }

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
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-sidebar-accent rounded-lg flex items-center justify-center">
                <Globe size={16} className="text-sidebar-accent-foreground" />
              </div>
              <span className="font-semibold text-lg hidden sm:inline">CIH</span>
            </Link>
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
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="w-full flex items-center justify-between px-2 py-2 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-sidebar-accent rounded-full flex items-center justify-center ring-2 ring-transparent group-hover:ring-sidebar-accent-foreground/20 transition-all">
                      <User size={16} className="text-sidebar-accent-foreground" />
                    </div>
                    <div className="text-left hidden sm:block">
                      <div className="text-sm font-semibold truncate max-w-[100px]">{user?.username || 'Utilisateur'}</div>
                      <div className="text-[10px] uppercase tracking-wider opacity-60 font-bold">{user?.role || 'Analyste'}</div>
                    </div>
                  </div>
                  <ChevronDown size={14} className="hidden sm:block opacity-50" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Mon Compte</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings" className="cursor-pointer flex items-center">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Paramètres</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer flex items-center">
                  <Bell className="mr-2 h-4 w-4" />
                  <span>Notifications</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive focus:text-destructive cursor-pointer flex items-center" onClick={logout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Déconnexion</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
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
            <h1 className="text-lg font-bold text-foreground">
              CIH <span className="text-primary">Intelligence</span>
            </h1>
          </div>

          {/* Top Right Actions */}
          <div className="flex items-center gap-4">
            <Link href="/alerts" className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground relative">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-card" />
            </Link>
            <button className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground">
              <Settings size={20} />
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
