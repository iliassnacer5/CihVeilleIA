'use client'

import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertCircle, TrendingUp, FileText, Database, CheckCircle2 } from 'lucide-react'
import { KPICard } from '@/components/kpi-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    default:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  }
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<any>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [kpiData, analyticsData, alertsData] = await Promise.all([
        api.getKpis(),
        api.getDashboardAnalytics(),
        api.getLatestAlerts()
      ])
      setKpis(kpiData)
      setAnalytics(analyticsData)
      setAlerts(alertsData)
    } catch (error: any) {
      console.error('Failed to load dashboard data:', error)

      // User-friendly error messages based on error type
      if (error.type === 'NETWORK_ERROR') {
        setError('Unable to connect to server. Please ensure the backend is running on port 8000.')
      } else if (error.type === 'TIMEOUT_ERROR') {
        setError('Request timed out. The server might be slow or unresponsive.')
      } else if (error.statusCode === 401) {
        setError('Authentication required. Please log in.')
      } else if (error.statusCode === 403) {
        setError('Access denied. You do not have permission to view this data.')
      } else if (error.statusCode >= 500) {
        setError('Server error. Please try again later.')
      } else {
        setError(error.message || 'Failed to load dashboard data. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="max-w-md w-full border-destructive">
          <CardHeader>
            <div className="flex items-center gap-3">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <div>
                <CardTitle className="text-destructive">Connection Error</CardTitle>
                <CardDescription>Unable to load dashboard data</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{error}</p>
            <div className="bg-muted p-3 rounded-md text-xs font-mono">
              <p>Troubleshooting:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Verify backend is running: <code>http://localhost:8000/health</code></li>
                <li>Check terminal for backend errors</li>
                <li>Ensure port 8000 is not blocked</li>
              </ul>
            </div>
            <Button onClick={loadData} className="w-full">
              <TrendingUp className="mr-2 h-4 w-4" />
              Retry Connection
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Monitored Sources"
            value={kpis?.monitored_sources?.toString() || "0"}
            subtitle="Active sources tracking"
            icon={<Database size={32} />}
          />
          <KPICard
            title="Documents (Month)"
            value={kpis?.documents_month?.toLocaleString() || "0"}
            subtitle="Collected this month"
            icon={<FileText size={32} />}
          />
          <KPICard
            title="Regulatory Updates"
            value={kpis?.regulatory_updates?.toString() || "0"}
            subtitle="Detected & processed"
            icon={<AlertCircle size={32} />}
          />
          <KPICard
            title="AI Processing"
            value={`${kpis?.ai_processing_rate || 0}%`}
            subtitle="System uptime"
            icon={<CheckCircle2 size={32} />}
          />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documents Over Time */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Documents Over Time</CardTitle>
            <CardDescription>Monthly document collection trend</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics?.documents_over_time || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="documents"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--chart-1))' }}
                  name="Documents"
                />
                <Line
                  type="monotone"
                  dataKey="alerts"
                  stroke="hsl(var(--chart-2))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--chart-2))' }}
                  name="Alerts"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribution by Theme */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Distribution by Theme</CardTitle>
            <CardDescription>Document categorization breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Pie
                  data={analytics?.distribution_by_theme || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.name} (${entry.value}%)`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(analytics?.distribution_by_theme || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={`hsl(var(--chart-${(index % 4) + 1}))`} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Latest Alerts */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Latest Alerts</CardTitle>
              <CardDescription>
                Most recent detected regulatory and market updates
              </CardDescription>
            </div>
            <Button variant="outline" size="sm">
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start gap-4 p-4 border border-border rounded-lg hover:bg-secondary transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-foreground text-sm mb-1">
                    {alert.title}
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    {alert.source} • {alert.timestamp}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getSeverityColor(alert.severity)}`}
                >
                  {alert.severity.charAt(0).toUpperCase() +
                    alert.severity.slice(1)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
