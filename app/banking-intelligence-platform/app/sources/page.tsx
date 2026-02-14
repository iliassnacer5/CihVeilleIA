'use client'

import React, { useState, useEffect } from 'react'
import { Plus, Edit2, Pause, Play, Trash2, Loader2, RefreshCcw, ShieldCheck, ShieldX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table'
import { api, Source } from '@/lib/api'

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingSource, setEditingSource] = useState<Source | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    type: 'Regulatory',
    frequency: 'Daily'
  })
  const [isSaving, setIsSaving] = useState(false)
  const [scrapingIds, setScrapingIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    const loadSources = async () => {
      try {
        const data = await api.getSources()
        setSources(data)
      } catch (error) {
        console.error('Failed to load sources:', error)
      } finally {
        setIsLoading(false)
      }
    }
    loadSources()
  }, [])

  const handleToggleStatus = (id: string) => {
    setSources(
      sources.map((source) =>
        source.id === id
          ? {
            ...source,
            status: source.status === 'Active' ? 'Paused' : 'Active',
          }
          : source
      )
    )
  }

  const handleDelete = (id: string) => {
    setSources(sources.filter((source) => source.id !== id))
  }

  const handleEdit = (source: Source) => {
    setEditingSource(source)
    setShowModal(true)
  }

  const handleAddNew = () => {
    setEditingSource(null)
    setFormData({
      name: '',
      url: '',
      type: 'Regulatory',
      frequency: 'Daily'
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      if (editingSource) {
        // Edit logic (not yet implemented on backend)
        setShowModal(false)
      } else {
        const newSource = await api.addSource(formData)
        setSources([...sources, newSource])
        setShowModal(false)
      }
    } catch (error) {
      console.error('Failed to save source:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleScrape = async (id: string) => {
    setScrapingIds((prev) => new Set(prev).add(id))
    try {
      await api.scrapeSource(id)
      // On pourrait recharger les sources ici pour mettre à jour la date
      const data = await api.getSources()
      setSources(data)
    } catch (error) {
      console.error('Failed to scrape source:', error)
    } finally {
      setScrapingIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Sources Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage monitored websites and data sources
          </p>
        </div>
        <Button onClick={handleAddNew} className="gap-2">
          <Plus size={18} />
          Add Source
        </Button>
      </div>

      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-lg">Monitored Sources</CardTitle>
          <CardDescription>
            {sources.length} sources currently being monitored
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable<Source>
            columns={[
              { key: 'name', label: 'Source Name', width: '25%' },
              { key: 'url', label: 'URL', width: '25%', render: (val) => <span className="text-xs truncate block max-w-xs">{val}</span> },
              {
                key: 'type',
                label: 'Type',
                width: '15%',
                render: (value) => (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${value === 'Regulatory'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      : value === 'Press'
                        ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                        : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      }`}
                  >
                    {value}
                  </span>
                ),
              },
              { key: 'frequency', label: 'Frequency', width: '10%' },
              {
                key: 'status',
                label: 'Status',
                width: '10%',
                render: (value) => (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${value === 'Active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                      }`}
                  >
                    {value}
                  </span>
                ),
              },
              {
                key: 'whitelisted',
                label: 'Whitelist',
                width: '12%',
                render: (value) => (
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${value
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                    }`}>
                    {value ? <ShieldCheck size={14} /> : <ShieldX size={14} />}
                    {value ? 'Autorisé' : 'Non autorisé'}
                  </span>
                ),
              },
              { key: 'lastUpdated', label: 'Last Updated', width: '15%' },
            ]}
            data={sources}
            rowKey="id"
            actions={(row) => (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleScrape(row.id)}
                  disabled={scrapingIds.has(row.id)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-accent hover:text-accent/80 disabled:opacity-50"
                  title="Scrape now"
                >
                  <RefreshCcw size={16} className={scrapingIds.has(row.id) ? 'animate-spin' : ''} />
                </button>
                <button
                  onClick={() => handleToggleStatus(row.id)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                  title={
                    row.status === 'Active'
                      ? 'Pause source'
                      : 'Resume source'
                  }
                >
                  {row.status === 'Active' ? (
                    <Pause size={16} />
                  ) : (
                    <Play size={16} />
                  )}
                </button>
                <button
                  onClick={() => handleEdit(row)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                  title="Edit source"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={() => handleDelete(row.id)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-destructive hover:text-red-600"
                  title="Delete source"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            )}
          />
        </CardContent>
      </Card>

      {/* Add/Edit Source Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-lg max-w-md w-full p-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">
              {editingSource ? 'Edit Source' : 'Add New Source'}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Source URL
                </label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://example.com/regulatory-news"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Source Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Basel Committee Official Website"
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option>Regulatory</option>
                  <option>Press</option>
                  <option>Market</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Frequency
                </label>
                <select
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option>Real-time</option>
                  <option>Hourly</option>
                  <option>Daily</option>
                  <option>Weekly</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  className="flex-1 bg-transparent"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleSave}
                  disabled={isSaving || !formData.name || !formData.url}
                >
                  {isSaving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : editingSource ? (
                    'Update'
                  ) : (
                    'Add'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
