'use client'

import React, { useState } from 'react'
import {
  Save,
  AlertCircle,
  Shield,
  Clock,
  Database,
  User,
  Plus,
  X,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'

interface WhitelistedDomain {
  id: number
  domain: string
  addedDate: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    refreshFrequency: 'hourly',
    confidenceThreshold: 85,
    dataRetentionDays: 365,
    enableNotifications: true,
  })

  const [whitelistedDomains, setWhitelistedDomains] = useState<WhitelistedDomain[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [newDomain, setNewDomain] = useState('')
  const [showDomainForm, setShowDomainForm] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  React.useEffect(() => {
    const loadData = async () => {
      try {
        const [settingsData, domainsData] = await Promise.all([
          api.getSettings(),
          api.getWhitelistedDomains(),
        ])
        setSettings(settingsData)
        setWhitelistedDomains(domainsData)
      } catch (error) {
        console.error('Failed to load settings:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [])

  const handleAddDomain = async () => {
    if (newDomain.trim() && !whitelistedDomains.some((d) => d.domain === newDomain)) {
      const newEntry = {
        id: Date.now(),
        domain: newDomain,
        addedDate: new Date().toISOString().split('T')[0],
      }
      try {
        await api.addWhitelistedDomain(newEntry)
        setWhitelistedDomains([...whitelistedDomains, newEntry])
        setNewDomain('')
        setShowDomainForm(false)
      } catch (error) {
        console.error('Failed to add domain:', error)
      }
    }
  }

  const handleRemoveDomain = (id: number) => {
    setWhitelistedDomains(whitelistedDomains.filter((d) => d.id !== id))
  }

  const handleSaveSettings = async () => {
    try {
      await api.updateSettings(settings)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-muted-foreground animate-pulse">Loading global settings...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure platform behavior and compliance settings
        </p>
      </div>

      {/* Legal Disclaimer */}
      <Card className="border border-border bg-blue-50 dark:bg-blue-950">
        <CardHeader>
          <div className="flex items-start gap-3">
            <AlertCircle className="text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" size={20} />
            <div>
              <CardTitle className="text-lg text-blue-900 dark:text-blue-100">
                Compliance & Legal
              </CardTitle>
              <CardDescription className="text-blue-800 dark:text-blue-200">
                Important information about web scraping and data collection
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-blue-900 dark:text-blue-100 space-y-3">
          <p>
            This platform collects data from publicly available sources. All
            web monitoring activities comply with:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>Robots.txt guidelines and website terms of service</li>
            <li>GDPR and data protection regulations</li>
            <li>Local regulations governing web data collection</li>
            <li>Rate limiting to avoid server overload</li>
          </ul>
          <p className="font-semibold">
            Organization is responsible for ensuring compliance with all
            applicable laws and regulations.
          </p>
        </CardContent>
      </Card>

      {/* General Settings */}
      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-lg">General Settings</CardTitle>
          <CardDescription>
            Configure refresh frequency and data quality thresholds
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              <Clock className="inline mr-2" size={16} />
              Refresh Frequency
            </label>
            <select
              value={settings.refreshFrequency}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  refreshFrequency: e.target.value,
                })
              }
              className="w-full px-4 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="real-time">Real-time (Continuous)</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
            <p className="text-xs text-muted-foreground mt-2">
              How often the system checks monitored sources for updates
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              <Shield className="inline mr-2" size={16} />
              AI Confidence Threshold
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="60"
                max="100"
                step="1"
                value={settings.confidenceThreshold}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    confidenceThreshold: parseInt(e.target.value),
                  })
                }
                className="w-full"
              />
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">
                  Minimum confidence level for accepting AI classifications
                </span>
                <span className="text-lg font-semibold text-accent">
                  {settings.confidenceThreshold}%
                </span>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-foreground mb-2">
              <Database className="inline mr-2" size={16} />
              Data Retention Period
            </label>
            <input
              type="number"
              value={settings.dataRetentionDays}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  dataRetentionDays: parseInt(e.target.value),
                })
              }
              className="w-full px-4 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p className="text-xs text-muted-foreground mt-2">
              Documents older than this number of days will be automatically
              archived
            </p>
          </div>

          <div className="flex items-center justify-between pt-2">
            <label className="text-sm font-semibold text-foreground flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableNotifications}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    enableNotifications: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-border cursor-pointer"
              />
              Enable Notifications
            </label>
            <span className="text-xs text-muted-foreground">
              Receive alerts for critical updates
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Source Whitelist */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Source Whitelist</CardTitle>
              <CardDescription>
                Approved domains for data collection
              </CardDescription>
            </div>
            <Button
              onClick={() => setShowDomainForm(!showDomainForm)}
              size="sm"
              className="gap-2"
            >
              <Plus size={16} />
              Add Domain
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {showDomainForm && (
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleAddDomain()
                }}
                placeholder="example.com"
                className="flex-1 px-4 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <Button onClick={handleAddDomain} size="sm">
                Add
              </Button>
              <Button
                onClick={() => setShowDomainForm(false)}
                variant="outline"
                size="sm"
              >
                Cancel
              </Button>
            </div>
          )}

          <div className="space-y-2">
            {whitelistedDomains.map((domain) => (
              <div
                key={domain.id}
                className="flex items-center justify-between p-3 border border-border rounded-lg"
              >
                <div>
                  <p className="font-medium text-foreground">{domain.domain}</p>
                  <p className="text-xs text-muted-foreground">
                    Added on {new Date(domain.addedDate).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleRemoveDomain(domain.id)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-destructive hover:text-red-600"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>

          {whitelistedDomains.length === 0 && (
            <p className="text-center text-muted-foreground py-4">
              No whitelisted domains yet
            </p>
          )}
        </CardContent>
      </Card>

      {/* Model Configuration */}
      <Card className="border border-border bg-secondary/30">
        <CardHeader>
          <CardTitle className="text-lg">Model Configuration</CardTitle>
          <CardDescription>
            AI model settings (Read-only for security)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-semibold text-muted-foreground">
                Active Model
              </p>
              <p className="text-sm font-medium text-foreground">
                GPT-4 Banking Edition
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground">
                Model Version
              </p>
              <p className="text-sm font-medium text-foreground">v2.1.4</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground">
                Last Updated
              </p>
              <p className="text-sm font-medium text-foreground">
                2024-02-01
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground">
                Status
              </p>
              <p className="text-sm font-medium text-accent">Active</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground pt-2">
            Contact your administrator to update model settings
          </p>
        </CardContent>
      </Card>

      {/* User Account */}
      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-lg">Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Full Name
              </label>
              <input
                type="text"
                defaultValue="John Doe"
                disabled
                className="w-full px-4 py-2 border border-border rounded-lg bg-secondary text-foreground disabled:opacity-60"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted-foreground mb-1">
                Email
              </label>
              <input
                type="email"
                defaultValue="john.doe@cihbank.com"
                disabled
                className="w-full px-4 py-2 border border-border rounded-lg bg-secondary text-foreground disabled:opacity-60"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1">
              Role
            </label>
            <input
              type="text"
              defaultValue="Risk Manager"
              disabled
              className="w-full px-4 py-2 border border-border rounded-lg bg-secondary text-foreground disabled:opacity-60"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Contact your administrator to change account settings
          </p>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        {saveSuccess && (
          <div className="flex items-center gap-2 text-accent text-sm font-medium">
            <Save size={16} />
            Settings saved successfully
          </div>
        )}
        <Button onClick={handleSaveSettings} className="gap-2">
          <Save size={18} />
          Save Settings
        </Button>
      </div>
    </div>
  )
}
