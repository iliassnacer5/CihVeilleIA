'use client'

import React, { useState, useEffect } from 'react'
import { Bell, Archive, Trash2, Clock, AlertTriangle, Loader2, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'

import { Alert as ApiAlert } from '@/lib/api'

type Alert = ApiAlert;

function getSeverityStyles(severity: string) {
  switch (severity.toLowerCase()) {
    case 'high': // aligned with api.ts capitalized or lowercase fallback
    case 'critical':
      return {
        bg: 'bg-red-100 dark:bg-red-900/30',
        text: 'text-red-800 dark:text-red-200',
        border: 'border-red-200 dark:border-red-700',
      }
    case 'medium':
      return {
        bg: 'bg-yellow-100 dark:bg-yellow-900/30',
        text: 'text-yellow-800 dark:text-yellow-200',
        border: 'border-yellow-200 dark:border-yellow-700',
      }
    default:
      return {
        bg: 'bg-blue-100 dark:bg-blue-900/30',
        text: 'text-blue-800 dark:text-blue-200',
        border: 'border-blue-200 dark:border-blue-700',
      }
  }
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterSeverity, setFilterSeverity] = useState<string>('all')
  const [filterRead, setFilterRead] = useState<string>('all')

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await api.getLatestAlerts()
        setAlerts(data)
      } catch (error) {
        console.error('Failed to load alerts:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadAlerts()
  }, [])

  const filteredAlerts = alerts.filter((alert) => {
    const severityMatch =
      filterSeverity === 'all' || alert.severity.toLowerCase() === filterSeverity.toLowerCase()
    const readMatch =
      filterRead === 'all' ||
      (filterRead === 'unread' && !alert.read) ||
      (filterRead === 'read' && alert.read)
    return severityMatch && readMatch
  })

  const unreadCount = alerts.filter((a) => !a.read).length
  const criticalCount = alerts.filter((a) => a.severity.toLowerCase() === 'high' || a.severity.toLowerCase() === 'critical').length

  const handleArchive = (id: string | number) => {
    setAlerts(alerts.filter((alert) => alert.id !== id))
  }

  const handleMarkAsRead = (id: string | number) => {
    setAlerts(
      alerts.map((alert) =>
        alert.id === id ? { ...alert, read: true } : alert
      )
    )
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-muted-foreground animate-pulse">Monitoring sources for updates...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            Alerts & Monitoring
          </h1>
          <p className="text-muted-foreground mt-1">
            Regulatory and market alerts detected from monitored sources
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary">
          <Bell size={20} className="text-accent" />
          <div className="text-center">
            <p className="text-sm font-semibold text-foreground">
              {unreadCount}
            </p>
            <p className="text-xs text-muted-foreground">Unread</p>
          </div>
        </div>
      </div>

      {/* Critical Alerts */}
      {criticalCount > 0 && (
        <div className="bg-red-100 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-red-800 dark:text-red-200 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-semibold text-red-800 dark:text-red-200">
                {criticalCount} Critical Alert{criticalCount !== 1 ? 's' : ''} Requires Immediate Attention
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                Please review and take appropriate action on all critical
                alerts below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <Card className="border border-border">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="text-sm font-semibold text-foreground block mb-2">
                Severity
              </label>
              <div className="flex gap-2">
                {['all', 'critical', 'high', 'medium', 'low'].map((level) => (
                  <button
                    key={level}
                    onClick={() => setFilterSeverity(level)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterSeverity === level
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-foreground hover:bg-secondary/80'
                      }`}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-semibold text-foreground block mb-2">
                Status
              </label>
              <div className="flex gap-2">
                {['all', 'unread', 'read'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilterRead(status)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filterRead === status
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-foreground hover:bg-secondary/80'
                      }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => {
            const styles = getSeverityStyles(alert.severity)
            return (
              <Card
                key={alert.id}
                className={`border transition-all ${alert.read
                  ? 'border-border'
                  : `${styles.border} ${styles.bg}`
                  }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-start gap-2 mb-1">
                        <h3
                          className={`font-semibold leading-tight ${alert.read
                            ? 'text-foreground'
                            : styles.text
                            }`}
                        >
                          {alert.title}
                        </h3>
                        {!alert.read && (
                          <span className="inline-block w-2 h-2 rounded-full bg-current flex-shrink-0 mt-2" />
                        )}
                      </div>

                      <p className="text-sm text-muted-foreground mb-2">
                        {alert.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-xs">
                        <span
                          className={`px-3 py-1 rounded-full font-medium ${alert.read
                            ? 'bg-secondary text-foreground'
                            : styles.text + ' ' + styles.bg
                            }`}
                        >
                          {alert.severity.charAt(0).toUpperCase() +
                            alert.severity.slice(1).toLowerCase()}
                        </span>
                        <span className="px-3 py-1 rounded-full bg-secondary text-foreground">
                          {alert.category}
                        </span>
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Clock size={14} />
                          {alert.timestamp}
                        </div>
                        <span className="text-muted-foreground">{alert.source}</span>
                      </div>
                    </div>

                    <div className="flex gap-2 flex-shrink-0">
                      {!alert.read && (
                        <button
                          onClick={() => handleMarkAsRead(alert.id)}
                          className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                          title="Mark as read"
                        >
                          <Bell size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleArchive(alert.id)}
                        className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                        title="Archive alert"
                      >
                        <Archive size={16} />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })
        ) : (
          <Card className="border border-border">
            <CardContent className="p-12 text-center">
              <p className="text-muted-foreground">No alerts match the current filters</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
