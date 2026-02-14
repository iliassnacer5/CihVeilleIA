'use client'

import React, { useState, useEffect } from 'react'
import { Shield, ShieldCheck, AlertTriangle, Search, Filter, Clock, User, Activity } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { api, AuditLog } from '@/lib/api'

// ── Helpers ──────────────────────────────────────────

/** Converts a Unix timestamp (seconds) to a readable French date string */
function formatTimestamp(ts: number | string): string {
    if (!ts) return '—'
    const date = new Date(typeof ts === 'string' ? parseFloat(ts) * 1000 : ts * 1000)
    if (isNaN(date.getTime())) return String(ts)
    return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    })
}

/** Extracts the display username from the audit log entry */
function getDisplayUser(log: AuditLog): string {
    // Try multiple paths since the backend stores user info in different places
    if (log.username && log.username !== 'system') return log.username
    if (log.user_id && log.user_id !== 'system') return log.user_id

    // Check inside the details object
    if (log.details && typeof log.details === 'object') {
        const d = log.details as Record<string, any>
        if (d.username) return d.username
        if (d.user) return d.user
        if (d.target_username) return d.target_username
    }

    return 'system'
}

/** Formats the event details object into a readable string */
function formatDetails(details: any): string {
    if (!details) return '—'
    if (typeof details === 'string') return details

    if (typeof details === 'object') {
        const parts: string[] = []
        const d = details as Record<string, any>

        // Pick the most useful fields to display
        if (d.username) parts.push(`Utilisateur: ${d.username}`)
        if (d.target_username) parts.push(`Cible: ${d.target_username}`)
        if (d.role) parts.push(`Rôle: ${d.role}`)
        if (d.ip_address && d.ip_address !== '0.0.0.0') parts.push(`IP: ${d.ip_address}`)
        if (d.reason) parts.push(`Raison: ${d.reason}`)
        if (d.error) parts.push(`Erreur: ${d.error}`)
        if (d.email) parts.push(`Email: ${d.email}`)
        if (d.doc_title) parts.push(`Doc: ${d.doc_title}`)
        if (d.priority) parts.push(`Priorité: ${d.priority}`)
        if (d.score) parts.push(`Score: ${d.score}`)
        if (d.changes) parts.push(`Modif: ${JSON.stringify(d.changes)}`)

        // If we found known fields, show them
        if (parts.length > 0) return parts.join(' • ')

        // Fallback: show all key-value pairs
        const fallback = Object.entries(d)
            .filter(([, v]) => v !== null && v !== undefined && v !== '')
            .map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
            .join(' • ')
        return fallback || '—'
    }

    return String(details)
}

/** Maps backend status values to display labels */
function normalizeStatus(status: string): 'Success' | 'Warning' | 'Failure' {
    const s = (status || '').toUpperCase()
    if (s === 'SUCCESS' || s === 'OK') return 'Success'
    if (s === 'WARNING' || s === 'WARN') return 'Warning'
    return 'Failure'
}

/** Formats an action string for display */
function formatAction(action: string): string {
    if (!action) return '—'
    return action.replace(/_/g, ' ')
}

// ── Component ────────────────────────────────────────

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [searchTerm, setSearchTerm] = useState('')
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const loadLogs = async () => {
            try {
                const data = await api.getAuditLogs()
                setLogs(Array.isArray(data) ? data : [])
            } catch (error) {
                console.error('Failed to load audit logs:', error)
            } finally {
                setIsLoading(false)
            }
        }
        loadLogs()
    }, [])

    const filteredLogs = logs.filter(log => {
        const term = searchTerm.toLowerCase()
        if (!term) return true
        return (
            (log.action || '').toLowerCase().includes(term) ||
            getDisplayUser(log).toLowerCase().includes(term) ||
            formatDetails(log.details).toLowerCase().includes(term) ||
            (log.module || '').toLowerCase().includes(term)
        )
    })

    // Stats
    const totalEvents = logs.length
    const failedEvents = logs.filter(l => normalizeStatus(l.status) === 'Failure').length
    const uniqueUsers = new Set(logs.map(l => getDisplayUser(l))).size

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Audit & Compliance Trail</h1>
                    <p className="text-muted-foreground mt-1">
                        Journal traçable de toutes les activités système
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="gap-2">
                        <ShieldCheck size={18} />
                        Compliance Export
                    </Button>
                </div>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                    <CardContent className="flex items-center gap-4 p-4">
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Activity size={20} className="text-primary" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{totalEvents}</p>
                            <p className="text-xs text-muted-foreground">Événements total</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center gap-4 p-4">
                        <div className="p-2 rounded-lg bg-red-500/10">
                            <AlertTriangle size={20} className="text-red-500" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{failedEvents}</p>
                            <p className="text-xs text-muted-foreground">Échecs détectés</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center gap-4 p-4">
                        <div className="p-2 rounded-lg bg-blue-500/10">
                            <User size={20} className="text-blue-500" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{uniqueUsers}</p>
                            <p className="text-xs text-muted-foreground">Utilisateurs actifs</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex items-center gap-4 bg-card p-4 rounded-lg border border-border">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                    <Input
                        placeholder="Rechercher par action, utilisateur ou détails..."
                        className="pl-10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <Button variant="secondary" className="gap-2">
                    <Filter size={18} />
                    Filtres
                </Button>
            </div>

            <Card className="border border-border">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Shield className="text-primary" size={20} />
                        <CardTitle className="text-lg">Security & Activity Logs</CardTitle>
                    </div>
                    <CardDescription>
                        {filteredLogs.length} événements affichés
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <DataTable<AuditLog>
                        columns={[
                            {
                                key: 'timestamp',
                                label: 'Date & Heure',
                                width: '18%',
                                render: (value) => (
                                    <span className="flex items-center gap-1.5 text-xs font-mono">
                                        <Clock size={12} className="text-muted-foreground" />
                                        {formatTimestamp(value)}
                                    </span>
                                ),
                            },
                            {
                                key: 'username',
                                label: 'Utilisateur',
                                width: '12%',
                                render: (_value, row) => (
                                    <span className="flex items-center gap-1.5">
                                        <User size={12} className="text-muted-foreground" />
                                        <span className="font-medium">{getDisplayUser(row as AuditLog)}</span>
                                    </span>
                                ),
                            },
                            {
                                key: 'action',
                                label: 'Action',
                                width: '14%',
                                render: (value) => (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-primary/10 text-primary text-xs font-semibold uppercase tracking-wider">
                                        {formatAction(value)}
                                    </span>
                                ),
                            },
                            {
                                key: 'status',
                                label: 'Statut',
                                width: '10%',
                                render: (value) => {
                                    const normalized = normalizeStatus(value)
                                    return (
                                        <span
                                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium w-fit ${normalized === 'Success'
                                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                                    : normalized === 'Warning'
                                                        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                                                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                                }`}
                                        >
                                            {normalized === 'Success' ? <ShieldCheck size={12} /> : normalized === 'Warning' ? <AlertTriangle size={12} /> : <Shield size={12} />}
                                            {normalized}
                                        </span>
                                    )
                                },
                            },
                            {
                                key: 'details',
                                label: 'Détails',
                                width: '46%',
                                render: (value) => (
                                    <span className="text-xs text-muted-foreground line-clamp-2">
                                        {formatDetails(value)}
                                    </span>
                                ),
                            },
                        ]}
                        data={filteredLogs}
                        rowKey="id"
                    />
                </CardContent>
            </Card>
        </div>
    )
}
