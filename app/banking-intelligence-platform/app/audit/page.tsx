'use client'

import React, { useState, useEffect } from 'react'
import { Shield, ShieldCheck, AlertTriangle, Info, Search, Filter } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

interface AuditLog {
    id: string
    timestamp: string
    user: string
    action: string
    module: string
    status: 'Success' | 'Warning' | 'Failure'
    details: string
}

// Mock data removed

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [searchTerm, setSearchTerm] = useState('')
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const loadLogs = async () => {
            try {
                const data = await api.getAuditLogs()
                setLogs(data)
            } catch (error) {
                console.error('Failed to load audit logs:', error)
            } finally {
                setIsLoading(false)
            }
        }
        loadLogs()
    }, [])

    const filteredLogs = logs.filter(log =>
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.user.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Audit & Compliance Trail</h1>
                    <p className="text-muted-foreground mt-1">
                        Traceable log of all system activities and user interventions
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="gap-2">
                        <ShieldCheck size={18} />
                        Compliance Export
                    </Button>
                </div>
            </div>

            <div className="flex items-center gap-4 bg-card p-4 rounded-lg border border-border">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                    <Input
                        placeholder="Search logs by action, user or details..."
                        className="pl-10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <Button variant="secondary" className="gap-2">
                    <Filter size={18} />
                    Filters
                </Button>
            </div>

            <Card className="border border-border">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Shield className="text-primary" size={20} />
                        <CardTitle className="text-lg">Security & Activity Logs</CardTitle>
                    </div>
                    <CardDescription>
                        Showing {filteredLogs.length} recent events
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <DataTable<AuditLog>
                        columns={[
                            { key: 'timestamp', label: 'Timestamp', width: '20%' },
                            { key: 'user', label: 'User/Subject', width: '15%' },
                            { key: 'action', label: 'Action', width: '15%' },
                            {
                                key: 'status',
                                label: 'Status',
                                width: '10%',
                                render: (value) => (
                                    <span
                                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${value === 'Success'
                                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                            : value === 'Warning'
                                                ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                                                : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                            }`}
                                    >
                                        {value === 'Success' ? <ShieldCheck size={12} /> : value === 'Warning' ? <AlertTriangle size={12} /> : <Shield size={12} />}
                                        {value}
                                    </span>
                                ),
                            },
                            { key: 'details', label: 'Event Details', width: '40%' },
                        ]}
                        data={filteredLogs}
                        rowKey="id"
                    />
                </CardContent>
            </Card>
        </div>
    )
}
