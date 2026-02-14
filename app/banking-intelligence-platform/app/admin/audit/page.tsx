'use client'

import React, { useState, useEffect } from 'react'
import {
    Search,
    Filter,
    Download,
    ShieldAlert,
    Calendar,
    User,
    Activity,
    CheckCircle2,
    XCircle,
    FileDown,
    Clock,
    ExternalLink
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/data-table'
import { api, auth } from '@/lib/api'
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
import { useAuth } from '@/app/context/AuthContext'
import { toast } from 'sonner'

interface AuditLog {
    id: string
    timestamp: string | number
    user_id: string
    username: string
    role: string
    action: string
    module: string
    status: string
    details: any
    ip_address?: string
}

export default function AuditLogsPage() {
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const { isAdmin } = useAuth()

    const fetchLogs = async () => {
        setLoading(true)
        try {
            const data = await api.get('/audit/logs', {
                params: { search: searchQuery || undefined }
            })
            setLogs(data)
        } catch (error) {
            console.error('Failed to fetch audit logs:', error)
            toast.error('Erreur lors du chargement des logs d\'audit')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isAdmin) {
            fetchLogs()
        }
    }, [isAdmin])

    const formatTimestamp = (ts: string | number) => {
        const date = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts)
        return date.toLocaleString()
    }

    const exportCSV = async () => {
        try {
            const token = auth.getToken();
            const response = await fetch(`${API_BASE_URL}/audit/export`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Export CSV téléchargé');
        } catch (error) {
            console.error('Export failed:', error);
            toast.error('Erreur lors de l\'export CSV');
        }
    }

    const columns = [
        {
            key: 'timestamp' as keyof AuditLog,
            label: 'Date & Heure',
            render: (value: any) => (
                <div className="flex items-center gap-2 text-muted-foreground whitespace-nowrap">
                    <Clock size={14} />
                    {formatTimestamp(value)}
                </div>
            )
        },
        {
            key: 'username' as keyof AuditLog,
            label: 'Utilisateur',
            render: (value: any, row: AuditLog) => (
                <div className="font-medium">
                    {value || 'System'}
                    {row.role && (
                        <span className="block text-[10px] uppercase opacity-60">
                            {row.role === 'ROLE_ADMIN' ? 'Admin' : 'Analyste'}
                        </span>
                    )}
                </div>
            )
        },
        {
            key: 'action' as keyof AuditLog,
            label: 'Action',
            render: (value: any, row: AuditLog) => (
                <div>
                    <span className="font-semibold">{value}</span>
                    <span className="block text-xs text-muted-foreground italic px-1 bg-secondary inline-block rounded">
                        {row.module}
                    </span>
                </div>
            )
        },
        {
            key: 'status' as keyof AuditLog,
            label: 'Statut',
            render: (value: any) => (
                <div className="flex items-center gap-2">
                    {value === 'SUCCESS' ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded flex items-center gap-1">
                            <CheckCircle2 size={12} /> OK
                        </span>
                    ) : (
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-bold rounded flex items-center gap-1">
                            <XCircle size={12} /> ERROR
                        </span>
                    )}
                </div>
            )
        },
        {
            key: 'ip_address' as keyof AuditLog,
            label: 'Adresse IP',
            render: (value: any) => (
                <code className="text-xs bg-secondary px-1.5 py-0.5 rounded text-muted-foreground">
                    {value || '0.0.0.0'}
                </code>
            )
        }
    ]

    if (!isAdmin) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
                <ShieldAlert size={48} className="text-destructive animate-pulse" />
                <h1 className="text-2xl font-bold">Accès Restreint</h1>
                <p className="text-muted-foreground">Seuls les administrateurs peuvent consulter les journaux d'audit.</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Audit & Conformité</h1>
                    <p className="text-muted-foreground">Historique complet des actions sensibles et événements de sécurité.</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="gap-2" onClick={exportCSV}>
                        <FileDown size={18} />
                        Exporter CSV
                    </Button>
                    <Button variant="ghost" size="icon" onClick={fetchLogs}>
                        <Activity size={18} />
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">Events (24h)</p>
                        <h3 className="text-2xl font-bold">{logs.length}</h3>
                    </div>
                    <div className="p-3 bg-secondary rounded-lg">
                        <Activity size={24} className="text-primary" />
                    </div>
                </div>
                <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">Échecs de sécurité</p>
                        <h3 className="text-2xl font-bold text-red-500">{logs.filter(l => l.status !== 'SUCCESS').length}</h3>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg">
                        <ShieldAlert size={24} className="text-red-500" />
                    </div>
                </div>
                <div className="bg-card border border-border p-4 rounded-xl flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">Utilisateurs Actifs</p>
                        <h3 className="text-2xl font-bold">4</h3>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                        <User size={24} className="text-blue-500" />
                    </div>
                </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
                <div className="flex items-center gap-4 mb-6">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                        <Input
                            placeholder="Rechercher une action, un utilisateur..."
                            className="pl-10"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <Button variant="outline" className="gap-2">
                        <Calendar size={18} />
                        Période
                    </Button>
                </div>

                <DataTable
                    columns={columns}
                    data={logs}
                    rowKey="timestamp"
                    actions={(row) => (
                        <Button variant="ghost" size="sm" onClick={() => toast.info(JSON.stringify(row.details, null, 2))}>
                            <ExternalLink size={14} />
                        </Button>
                    )}
                />
            </div>
        </div>
    )
}
