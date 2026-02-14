'use client'

import React, { useState, useEffect } from 'react'
import {
    Mail,
    Plus,
    Trash2,
    RefreshCw,
    CheckCircle2,
    XCircle,
    MoreVertical,
    Settings as SettingsIcon,
    ShieldCheck,
    AlertTriangle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { DataTable } from '@/components/data-table'
import { toast } from 'sonner'
import { auth } from '@/lib/api'

interface EmailAccount {
    id: string
    email_address: string
    display_name: string
    smtp_host: string
    smtp_port: number
    username: string
    enabled: boolean
    is_default: boolean
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function EmailManagementPage() {
    const [accounts, setAccounts] = useState<EmailAccount[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isTesting, setIsTesting] = useState(false)

    const [formData, setFormData] = useState({
        email_address: '',
        display_name: '',
        smtp_host: 'smtp.office365.com',
        smtp_port: 587,
        username: '',
        password: '',
        enabled: true,
        is_default: false
    })

    useEffect(() => {
        fetchAccounts()
    }, [])

    const fetchAccounts = async () => {
        setIsLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/admin/emails`, {
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`
                }
            })
            if (response.ok) {
                const data = await response.json()
                setAccounts(data)
            } else {
                toast.error("Erreur lors de la récupération des comptes")
            }
        } catch (error) {
            console.error(error)
            toast.error("Échec de la connexion au serveur")
        } finally {
            setIsLoading(false)
        }
    }

    const handleTestConnection = async (accountId?: string) => {
        setIsTesting(true)
        try {
            let response;
            if (accountId) {
                response = await fetch(`${API_BASE_URL}/admin/emails/${accountId}/test`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${auth.getToken()}` }
                })
            } else {
                response = await fetch(`${API_BASE_URL}/admin/emails/test-params`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${auth.getToken()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                })
            }

            const result = await response.json()
            if (result.success) {
                toast.success(result.message || "Connexion SMTP réussie !")
            } else {
                toast.error(result.message || "Échec du test SMTP")
            }
        } catch (error) {
            toast.error("Erreur technique lors du test")
        } finally {
            setIsTesting(false)
        }
    }

    const handleCreateAccount = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const response = await fetch(`${API_BASE_URL}/admin/emails`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })

            if (response.ok) {
                toast.success("Compte ajouté avec succès")
                setIsModalOpen(false)
                fetchAccounts()
                setFormData({
                    email_address: '',
                    display_name: '',
                    smtp_host: 'smtp.office365.com',
                    smtp_port: 587,
                    username: '',
                    password: '',
                    enabled: true,
                    is_default: false
                })
            } else {
                const err = await response.json()
                toast.error(err.detail || "Erreur lors de la création")
            }
        } catch (error) {
            toast.error("Échec de la requête")
        }
    }

    const handleToggleStatus = async (account: EmailAccount) => {
        try {
            const response = await fetch(`${API_BASE_URL}/admin/emails/${account.id}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${auth.getToken()}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled: !account.enabled })
            })
            if (response.ok) {
                toast.success(`Compte ${account.enabled ? 'désactivé' : 'activé'}`)
                fetchAccounts()
            }
        } catch (error) {
            toast.error("Erreur lors de la modification")
        }
    }

    const handleDeleteAccount = async (id: string) => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer ce compte ?")) return
        try {
            const response = await fetch(`${API_BASE_URL}/admin/emails/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${auth.getToken()}` }
            })
            if (response.ok) {
                toast.success("Compte supprimé")
                fetchAccounts()
            }
        } catch (error) {
            toast.error("Erreur lors de la suppression")
        }
    }

    const columns = [
        {
            key: 'email_address' as keyof EmailAccount,
            label: 'Email / Utilisateur',
            render: (_: any, account: EmailAccount) => (
                <div className="flex flex-col">
                    <span className="font-medium">{account.display_name}</span>
                    <span className="text-xs text-muted-foreground">{account.email_address}</span>
                </div>
            )
        },
        {
            key: 'smtp_host' as keyof EmailAccount,
            label: 'Serveur SMTP',
            render: (_: any, account: EmailAccount) => (
                <div className="text-sm">
                    {account.smtp_host}:{account.smtp_port}
                </div>
            )
        },
        {
            key: 'enabled' as keyof EmailAccount,
            label: 'Statut',
            render: (_: any, account: EmailAccount) => (
                <div className="flex items-center gap-2">
                    <Badge variant={account.enabled ? 'default' : 'secondary'}>
                        {account.enabled ? 'Actif' : 'Inactif'}
                    </Badge>
                    {account.is_default && (
                        <Badge variant="outline" className="border-primary text-primary">Défaut</Badge>
                    )}
                </div>
            )
        }
    ]

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Email & Notifications</h1>
                    <p className="text-muted-foreground">Gérez les comptes Outlook pour l'envoi des alertes de veille.</p>
                </div>
                <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                    <DialogTrigger asChild>
                        <Button className="gap-2">
                            <Plus size={18} />
                            Ajouter un compte
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                        <form onSubmit={handleCreateAccount}>
                            <DialogHeader>
                                <DialogTitle>Configurer un nouveau compte Outlook</DialogTitle>
                                <DialogDescription>
                                    Paramétrez les accès SMTP sécurisés pour les notifications bancaires.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="display_name">Nom affiché</Label>
                                        <Input
                                            id="display_name"
                                            placeholder="Veille CIH Bank"
                                            required
                                            value={formData.display_name}
                                            onChange={e => setFormData({ ...formData, display_name: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Adresse Email</Label>
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="alerts@cih.ma"
                                            required
                                            value={formData.email_address}
                                            onChange={e => setFormData({ ...formData, email_address: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="smtp_host">Hôte SMTP</Label>
                                        <Input
                                            id="smtp_host"
                                            value={formData.smtp_host}
                                            onChange={e => setFormData({ ...formData, smtp_host: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="smtp_port">Port</Label>
                                        <Input
                                            id="smtp_port"
                                            type="number"
                                            value={formData.smtp_port}
                                            onChange={e => setFormData({ ...formData, smtp_port: parseInt(e.target.value) })}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="username">Nom d'utilisateur SMTP</Label>
                                    <Input
                                        id="username"
                                        required
                                        value={formData.username}
                                        onChange={e => setFormData({ ...formData, username: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="password">Mot de passe / Token</Label>
                                    <Input
                                        id="password"
                                        type="password"
                                        required
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                    />
                                </div>
                                <div className="flex items-center space-x-2 pt-2">
                                    <Switch
                                        id="is_default"
                                        checked={formData.is_default}
                                        onCheckedChange={checked => setFormData({ ...formData, is_default: checked })}
                                    />
                                    <Label htmlFor="is_default">Définir comme compte par défaut</Label>
                                </div>
                            </div>
                            <DialogFooter className="gap-2 sm:gap-0">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => handleTestConnection()}
                                    disabled={isTesting}
                                >
                                    {isTesting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                                    Tester Connexion
                                </Button>
                                <Button type="submit">Enregistrer le compte</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2">
                    <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
                        <DataTable
                            columns={columns}
                            data={accounts}
                            rowKey="id"
                            actions={(account: EmailAccount) => (
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => handleTestConnection(account.id)}
                                        title="Tester la connexion"
                                        disabled={isTesting}
                                    >
                                        <RefreshCw className={`h-4 w-4 ${isTesting ? 'animate-spin' : ''}`} />
                                    </Button>
                                    <Switch
                                        checked={account.enabled}
                                        onCheckedChange={() => handleToggleStatus(account)}
                                    />
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem onClick={() => handleDeleteAccount(account.id)} className="text-destructive">
                                                <Trash2 className="mr-2 h-4 w-4" />
                                                Supprimer
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            )}
                        />
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-primary/5 rounded-xl p-6 border border-primary/20">
                        <div className="flex items-center gap-3 mb-4 text-primary">
                            <ShieldCheck size={24} />
                            <h3 className="font-bold">Sécurité Bancaire</h3>
                        </div>
                        <p className="text-sm text-primary/80 leading-relaxed">
                            Tous les mots de passe SMTP sont chiffrés en <strong>AES-256</strong> avant stockage.
                            Ils ne sont jamais exposés via l'API. Seul le service de notification peut les déchiffrer temporairement pour l'envoi.
                        </p>
                    </div>

                    <div className="bg-amber-50 dark:bg-amber-950/20 rounded-xl p-6 border border-amber-200 dark:border-amber-900/50">
                        <div className="flex items-center gap-3 mb-4 text-amber-600 dark:text-amber-500">
                            <AlertTriangle size={24} />
                            <h3 className="font-bold">Rotation & Fallback</h3>
                        </div>
                        <p className="text-sm text-amber-600/80 dark:text-amber-500/80 leading-relaxed">
                            Si le compte par défaut échoue à l'envoi, le système tentera automatiquement d'utiliser un autre compte actif
                            pour garantir la continuité de la veille réglementaire.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
