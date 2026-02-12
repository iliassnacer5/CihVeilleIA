'use client'

import React, { useState, useEffect } from 'react'
import { ChevronRight, ExternalLink, Calendar, Zap, Upload, Loader2, Sparkles, BookOpen, Tag, Users, CheckCircle, Brain, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table'
import { api } from '@/lib/api'

import { Document as ApiDocument, DocumentDetail as ApiDocumentDetail, SummarizeResponse } from '@/lib/api'

type Document = ApiDocument;
type DocumentDetail = ApiDocumentDetail;

function getThemeColor(theme: string) {
  switch (theme) {
    case 'Regulation':
    case 'réglementation bancaire':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    case 'Market':
    case 'innovation et fintech':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    case 'Credit':
    case 'risque de crédit':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
    case 'cybersécurité':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    case 'lutte contre le blanchiment (LCB-FT)':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
    case 'durabilité et finance verte':
      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200'
    default:
      return 'bg-secondary text-foreground'
  }
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null)
  const [viewType, setViewType] = useState<'list' | 'detail'>('list')
  const [isLoading, setIsLoading] = useState(true)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isSummarizing, setIsSummarizing] = useState(false)
  const [synthesis, setSynthesis] = useState<SummarizeResponse | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isDeleting, setIsDeleting] = useState(false)

  const loadDocuments = async () => {
    setIsLoading(true)
    try {
      const data = await api.getDocuments()
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  const handleViewDetail = async (docId: string) => {
    setIsDetailLoading(true)
    setViewType('detail')
    setSynthesis(null) // Reset synthesis when viewing a new doc
    try {
      const detail = await api.getDocumentDetail(docId)
      setSelectedDoc(detail)
    } catch (error) {
      console.error('Failed to load document detail:', error)
    } finally {
      setIsDetailLoading(false)
    }
  }

  const handleBackToList = () => {
    setViewType('list')
    setSelectedDoc(null)
    setSynthesis(null)
  }

  const handleSummarize = async () => {
    if (!selectedDoc) return
    setIsSummarizing(true)
    try {
      const result = await api.summarizeDocument(selectedDoc.id)
      setSynthesis(result)
      // Update the selected doc with new enrichment data
      setSelectedDoc(prev => prev ? {
        ...prev,
        summary: result.summary,
        theme: result.topics[0] || prev.theme,
        entities: result.entities,
        confidence: result.confidence
      } : null)
    } catch (error) {
      console.error('Failed to summarize document:', error)
      alert('Erreur lors de la synthèse. Veuillez réessayer.')
    } finally {
      setIsSummarizing(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      await api.uploadDocument(file)
      await loadDocuments()
      alert('Document uploaded and indexed successfully!')
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Failed to upload document.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDelete = async (docId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) return

    setIsDeleting(true)
    try {
      await api.deleteDocument(docId)
      await loadDocuments()
      if (selectedDoc?.id === docId) handleBackToList()
    } catch (error) {
      console.error('Delete failed:', error)
      alert('Échec de la suppression.')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleBulkDelete = async () => {
    const count = selectedIds.size
    if (!confirm(`Êtes-vous sûr de vouloir supprimer les ${count} documents sélectionnés ?`)) return

    setIsDeleting(true)
    try {
      await api.bulkDeleteDocuments(Array.from(selectedIds))
      setSelectedIds(new Set())
      await loadDocuments()
    } catch (error) {
      console.error('Bulk delete failed:', error)
      alert('Échec de la suppression groupée.')
    } finally {
      setIsDeleting(false)
    }
  }

  if (viewType === 'detail') {
    if (isDetailLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <Loader2 className="animate-spin text-accent" size={48} />
          <p className="text-muted-foreground animate-pulse">Analyzing document content with AI...</p>
        </div>
      )
    }

    if (!selectedDoc) {
      return (
        <div className="text-center py-20">
          <p className="text-muted-foreground">Document not found.</p>
          <Button onClick={handleBackToList} variant="link">Back to list</Button>
        </div>
      )
    }

    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center justify-between">
          <button
            onClick={handleBackToList}
            className="flex items-center gap-2 text-accent hover:text-accent/80 transition-colors text-sm font-medium"
          >
            <ChevronRight size={16} className="rotate-180" />
            Back to Documents
          </button>

          {/* RÉSUMER BUTTON */}
          <Button
            onClick={handleSummarize}
            disabled={isSummarizing}
            className="relative overflow-hidden group"
            style={{
              background: isSummarizing
                ? undefined
                : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
              color: 'white',
              border: 'none',
            }}
          >
            {isSummarizing ? (
              <>
                <Loader2 className="animate-spin mr-2" size={18} />
                Analyse IA en cours...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 group-hover:animate-pulse" size={18} />
                Résumer avec l&apos;IA
              </>
            )}
            <span
              className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            />
          </Button>
        </div>

        <div className="space-y-4">
          <h1 className="text-3xl font-bold text-foreground">{selectedDoc.title}</h1>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar size={16} />
              {new Date(selectedDoc.date).toLocaleDateString()}
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getThemeColor(selectedDoc.theme)}`}>
              {selectedDoc.theme}
            </span>
            <div className="flex items-center gap-2 text-sm text-accent font-medium">
              <Zap size={16} />
              {selectedDoc.confidence}% confidence
            </div>
            {selectedDoc.url && (
              <a
                href={selectedDoc.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-accent hover:text-accent/80 transition-colors"
              >
                <ExternalLink size={16} />
                View Original
              </a>
            )}
          </div>
        </div>

        {/* AI SYNTHESIS PANEL */}
        {synthesis && (
          <div className="animate-in fade-in slide-in-from-top-4 duration-700">
            <Card className="border-2 border-purple-500/30 bg-gradient-to-br from-purple-500/5 via-transparent to-indigo-500/5 shadow-lg shadow-purple-500/5">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600">
                    <Brain className="text-white" size={20} />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Synthèse IA</CardTitle>
                    <CardDescription>Analyse automatique générée par Intelligence Artificielle</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Summary */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <BookOpen size={15} className="text-purple-500" />
                    Résumé
                  </div>
                  <p className="text-foreground leading-relaxed pl-6 border-l-2 border-purple-500/30">
                    {synthesis.summary}
                  </p>
                </div>

                {/* Topics */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <Tag size={15} className="text-indigo-500" />
                    Thématiques identifiées
                  </div>
                  <div className="flex flex-wrap gap-2 pl-6">
                    {synthesis.topics.map((topic, idx) => (
                      <span
                        key={idx}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium ${getThemeColor(topic)}`}
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Key Facts */}
                {synthesis.key_facts.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                      <CheckCircle size={15} className="text-green-500" />
                      Faits clés
                    </div>
                    <ul className="space-y-2 pl-6">
                      {synthesis.key_facts.map((fact, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-foreground/90">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
                          {fact}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Entities */}
                {synthesis.entities.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                      <Users size={15} className="text-blue-500" />
                      Entités détectées
                    </div>
                    <div className="flex flex-wrap gap-2 pl-6">
                      {synthesis.entities.map((entity, idx) => (
                        <span key={idx} className="px-3 py-1.5 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200 font-medium">
                          {entity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Confidence */}
                <div className="flex items-center gap-3 pt-2 border-t border-border/50">
                  <span className="text-xs text-muted-foreground">Confiance IA:</span>
                  <div className="flex-1 max-w-xs bg-secondary rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-1000 ease-out"
                      style={{
                        width: `${synthesis.confidence}%`,
                        background: 'linear-gradient(90deg, #6366f1, #a855f7)',
                      }}
                    />
                  </div>
                  <span className="text-xs font-bold text-foreground">{synthesis.confidence}%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* SUMMARIZING LOADING STATE */}
        {isSummarizing && (
          <Card className="border border-purple-500/20 animate-pulse">
            <CardContent className="py-12 flex flex-col items-center gap-4">
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-purple-500/20 w-16 h-16" />
                <div className="relative p-4 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600">
                  <Brain className="text-white animate-pulse" size={24} />
                </div>
              </div>
              <div className="text-center space-y-2">
                <p className="font-semibold text-foreground">Analyse IA en cours...</p>
                <p className="text-sm text-muted-foreground">Classification, résumé et extraction d&apos;entités</p>
                <p className="text-xs text-muted-foreground">(La première exécution peut prendre 1-2 minutes pour charger les modèles)</p>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="text-lg">AI-Generated Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed whitespace-pre-wrap">{selectedDoc.summary}</p>
              </CardContent>
            </Card>

            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="text-lg">Full Content</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed whitespace-pre-wrap max-h-[600px] overflow-y-auto pr-2">{selectedDoc.content}</p>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="text-lg">Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">Source</p>
                  <p className="text-foreground">{selectedDoc.source}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">Published</p>
                  <p className="text-foreground">{new Date(selectedDoc.date).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1">AI Confidence</p>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-accent h-2 rounded-full transition-all"
                      style={{ width: `${selectedDoc.confidence}%` }}
                    />
                  </div>
                  <p className="text-sm text-foreground mt-1">{selectedDoc.confidence}%</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-border">
              <CardHeader>
                <CardTitle className="text-lg">Extracted Entities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.entities && selectedDoc.entities.length > 0 ? (
                    selectedDoc.entities.map((entity, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-full text-xs bg-secondary text-foreground">
                        {entity}
                      </span>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground italic">No entities detected. Click &quot;Résumer&quot; to analyze.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Collected Documents</h1>
          <p className="text-muted-foreground mt-1">Browse and analyze documents from monitored sources</p>
        </div>
        <div className="flex items-center gap-3">
          {selectedIds.size > 0 && (
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
              disabled={isDeleting}
              className="gap-2 animate-in fade-in zoom-in duration-300"
            >
              {isDeleting ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
              Supprimer ({selectedIds.size})
            </Button>
          )}
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleFileUpload}
            disabled={isUploading}
          />
          <Button
            asChild
            disabled={isUploading}
            className="cursor-pointer"
          >
            <label htmlFor="file-upload" className="flex items-center gap-2">
              {isUploading ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <Upload size={18} />
              )}
              {isUploading ? 'Uploading...' : 'Upload Document'}
            </label>
          </Button>
        </div>
      </div>

      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-lg">Documents</CardTitle>
          <CardDescription>{documents.length} documents indexed</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable<Document>
            columns={[
              {
                key: 'title',
                label: 'Title',
                width: '40%',
                render: (value) => (
                  <span className="font-medium text-foreground line-clamp-1">{String(value)}</span>
                ),
              },
              { key: 'source', label: 'Source', width: '20%' },
              {
                key: 'date',
                label: 'Date',
                width: '15%',
                render: (value) => new Date(String(value)).toLocaleDateString(),
              },
              {
                key: 'theme',
                label: 'Theme',
                width: '15%',
                render: (value) => (
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getThemeColor(String(value))}`}>
                    {String(value)}
                  </span>
                ),
              },
              {
                key: 'confidence',
                label: 'Confidence',
                width: '10%',
                render: (value) => (
                  <span className="text-sm text-foreground">{String(value)}%</span>
                ),
              },
            ]}
            data={documents}
            rowKey="id"
            selectedKeys={selectedIds}
            onSelectionChange={setSelectedIds}
            actions={(row) => (
              <div className="flex items-center gap-2 justify-end">
                <button
                  onClick={() => handleViewDetail(row.id)}
                  className="p-2 hover:bg-secondary rounded-lg transition-colors text-accent"
                  title="Voir les détails"
                >
                  <ChevronRight size={18} />
                </button>
                <button
                  onClick={() => handleDelete(row.id)}
                  className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors text-destructive"
                  title="Supprimer"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            )}
          />
        </CardContent>
      </Card>
    </div>
  )
}

