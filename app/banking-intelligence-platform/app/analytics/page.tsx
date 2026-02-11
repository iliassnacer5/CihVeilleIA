'use client'

import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { KPICard } from '@/components/kpi-card'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, Zap, Target, Clock, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

export default function AnalyticsPage() {
  const [kpis, setKpis] = useState<any>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [kpiData, analyticsData] = await Promise.all([
          api.getKpis(),
          api.getDashboardAnalytics()
        ])
        setKpis(kpiData)
        setAnalytics(analyticsData)
      } catch (error) {
        console.error('Failed to load analytics:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-muted-foreground animate-pulse">Loading analytics engine...</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Analytics & KPIs</h1>
        <p className="text-muted-foreground mt-1">
          Monitor AI system performance and platform adoption metrics
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Monitored Sources"
          value={kpis?.monitored_sources || '0'}
          subtitle="Active web monitored targets"
          icon={<Zap size={32} />}
        />
        <KPICard
          title="AI Processing Rate"
          value={`${kpis?.ai_processing_rate || 0}%`}
          subtitle="Real-time enrichment speed"
          icon={<Target size={32} />}
        />
        <KPICard
          title="Documents (Month)"
          value={kpis?.documents_month || '0'}
          subtitle="Cumulative this cycle"
          icon={<Clock size={32} />}
        />
        <KPICard
          title="Regulatory Updates"
          value={kpis?.regulatory_updates || '0'}
          subtitle="Critical changes detected"
          icon={<TrendingUp size={32} />}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Processing Volume */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Document Volume Trend</CardTitle>
            <CardDescription>
              Processing throughput over the last 6 months
            </CardDescription>
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
                  name="Alerts"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Theme Distribution */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-lg">Distribution by Theme</CardTitle>
            <CardDescription>
              Volume of intelligence by regulatory theme
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics?.distribution_by_theme || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Bar
                  dataKey="value"
                  fill="hsl(var(--chart-1))"
                  name="Count"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Performance Summary */}
      <Card className="border border-border bg-secondary/30">
        <CardHeader>
          <CardTitle className="text-lg">System Performance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm font-semibold text-muted-foreground mb-2">
                Processing Efficiency
              </p>
              <p className="text-2xl font-bold text-accent">{kpis?.documents_month || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">
                documents processed this month
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-muted-foreground mb-2">
                Average Processing Time
              </p>
              <p className="text-2xl font-bold text-primary">{kpis?.avg_processing_time || '1.1s'}</p>
              <p className="text-xs text-muted-foreground mt-1">
                per document including AI analysis
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-muted-foreground mb-2">
                System Health
              </p>
              <p className="text-2xl font-bold text-green-500">{kpis?.system_health || '99.9%'}</p>
              <p className="text-xs text-muted-foreground mt-1">
                SLA for ingestion & analysis
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
