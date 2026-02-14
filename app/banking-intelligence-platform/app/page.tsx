'use client'

import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertCircle, TrendingUp, FileText, Database, CheckCircle2 } from 'lucide-react'
import { KPICard } from '@/components/kpi-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useAuth } from '@/app/context/AuthContext'
import { Search, MessageSquare, Globe, Bell } from 'lucide-react'
import Link from 'next/link'

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
  const { user, isAdmin } = useAuth()

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

  if (!isAdmin) {
    return (
      <div className="space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Bienvenue, {user?.username}</h1>
            <p className="text-muted-foreground">Voici votre espace de veille stratégique.</p>
          </div>
          <div className="flex gap-2 text-xs font-mono uppercase tracking-widest opacity-50 bg-secondary px-3 py-1 rounded-full items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2" />
            Mode Analyste
          </div>
        </div>

        {/* Quick Actions for User */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/search" className="group">
            <Card className="hover:border-primary transition-all cursor-pointer h-full group-hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Recherche Sémantique</CardTitle>
                <Search size={20} className="text-muted-foreground group-hover:text-primary transition-colors" />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">Explorez la base de connaissances via notre moteur IA.</p>
              </CardContent>
            </Card>
          </Link>
          <Link href="/chatbot" className="group">
            <Card className="hover:border-primary transition-all cursor-pointer h-full group-hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Assistant AI Chat</CardTitle>
                <MessageSquare size={20} className="text-muted-foreground group-hover:text-primary transition-colors" />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">Interrogez directement les documents par chat interactif.</p>
              </CardContent>
            </Card>
          </Link>
          <Link href="/documents" className="group">
            <Card className="hover:border-primary transition-all cursor-pointer h-full group-hover:shadow-md">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Documents Collectés</CardTitle>
                <FileText size={20} className="text-muted-foreground group-hover:text-primary transition-colors" />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">Consultez les dernières analyses et veilles extraites.</p>
              </CardContent>
            </Card>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Latest Alerts for User */}
          <Card className="lg:col-span-2 border border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Alertes Récentes</CardTitle>
                  <CardDescription>Mises à jour réglementaires et marché</CardDescription>
                </div>
                <Link href="/alerts">
                  <Button variant="ghost" size="sm">Voir tout</Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.length > 0 ? alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start gap-4 p-4 border border-border rounded-lg hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-foreground text-sm mb-1">{alert.title}</h4>
                      <p className="text-xs text-muted-foreground">{alert.source} • {alert.timestamp}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${getSeverityColor(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </div>
                )) : (
                  <div className="text-center py-8 text-muted-foreground">Aucune alerte récente.</div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* User Stats/Shortcuts */}
          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Documents du mois</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{kpis?.documents_month || 0}</div>
                <p className="text-xs text-muted-foreground text-green-500 flex items-center mt-1">
                  <TrendingUp size={12} className="mr-1" /> +12% vs mois dernier
                </p>
              </CardContent>
            </Card>
            <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <AlertCircle size={16} className="text-primary" /> Rappels IA
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  La nouvelle réglementation BAM sur le Open Banking est prioritaire cette semaine.
                </p>
                <Button variant="link" size="sm" className="px-0 h-auto text-primary text-xs mt-2">En savoir plus</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-foreground">Dashboard Administrateur</h1>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="w-2 h-2 bg-green-500 rounded-full" />
            Serveur Backend : OK
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Sources Surveillées"
            value={kpis?.monitored_sources?.toString() || "0"}
            subtitle="Connecteurs actifs"
            icon={<Database size={32} />}
          />
          <KPICard
            title="Documents (Mois)"
            value={kpis?.documents_month?.toLocaleString() || "0"}
            subtitle="Collectés ce mois"
            icon={<FileText size={32} />}
          />
          <KPICard
            title="Mises à jour Rég."
            value={kpis?.regulatory_updates?.toString() || "0"}
            subtitle="Détectées & traitées"
            icon={<AlertCircle size={32} />}
          />
          <KPICard
            title="Traitement IA"
            value={`${kpis?.ai_processing_rate || 0}%`}
            subtitle="Taux de succès"
            icon={<CheckCircle2 size={32} />}
          />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documents Over Time */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Tendances de Collecte</CardTitle>
            <CardDescription>Documents et alertes générés sur 6 mois</CardDescription>
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
                  name="Alertes"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribution by Theme */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Distribution par Thématique</CardTitle>
            <CardDescription>Répartition IA des contenus analysés</CardDescription>
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
      <Card className="border border-border shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-primary">Dernières Alertes Système</CardTitle>
              <CardDescription>
                Surveillance en temps réel des flux entrants
              </CardDescription>
            </div>
            <Link href="/audit">
              <Button variant="outline" size="sm">
                Consulter l'Audit
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start gap-4 p-4 border border-border rounded-lg hover:bg-secondary/50 transition-colors"
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
                  className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase whitespace-nowrap ${getSeverityColor(alert.severity)}`}
                >
                  {alert.severity}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
