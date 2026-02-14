'use client'

import React, { useState, useEffect } from 'react'
import {
    UserPlus,
    Search,
    Filter,
    MoreVertical,
    Shield,
    User as UserIcon,
    Trash2,
    CheckCircle2,
    XCircle,
    RefreshCw,
    Mail,
    Calendar,
    Lock
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/data-table'
import { api, User } from '@/lib/api'
import { useAuth } from '@/app/context/AuthContext'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { toast } from 'sonner'

export default function UserManagementPage() {
    const [users, setUsers] = useState<User[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [roleFilter, setRoleFilter] = useState('all')
    const [isAddUserOpen, setIsAddUserOpen] = useState(false)
    const [newUser, setNewUser] = useState({
        username: '',
        email: '',
        password: '',
        role: 'ROLE_USER'
    })
    const { isAdmin } = useAuth()

    const fetchUsers = async () => {
        setLoading(true)
        try {
            const data = await api.get('/admin/users', {
                params: {
                    search: searchQuery || undefined,
                    role: roleFilter === 'all' ? undefined : roleFilter
                }
            })
            setUsers(data)
        } catch (error) {
            console.error('Failed to fetch users:', error)
            toast.error('Erreur lors du chargement des utilisateurs')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isAdmin) {
            fetchUsers()
        }
    }, [isAdmin, roleFilter])

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        fetchUsers()
    }

    const toggleUserStatus = async (user: User) => {
        try {
            await api.patch(`/admin/users/${user.username}`, { is_active: !user.is_active })
            toast.success(`Utilisateur ${user.username} ${!user.is_active ? 'activé' : 'désactivé'}`)
            fetchUsers()
        } catch (error) {
            toast.error('Échec de la mise à jour')
        }
    }

    const deleteUser = async (username: string) => {
        if (!confirm(`Êtes-vous sûr de vouloir supprimer ${username} ?`)) return
        try {
            await api.delete(`/admin/users/${username}`)
            toast.success('Utilisateur supprimé')
            fetchUsers()
        } catch (error) {
            toast.error('Échec de la suppression')
        }
    }

    const resetPassword = async (username: string) => {
        try {
            const res = await api.post(`/admin/users/${username}/reset-password`, {})
            toast.success(`Nouveau mot de passe pour ${username}: ${res.new_password}`, {
                duration: 10000,
            })
        } catch (error) {
            toast.error('Échec de la réinitialisation')
        }
    }

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            await api.post('/admin/users', newUser)
            toast.success('Utilisateur créé avec succès')
            setIsAddUserOpen(false)
            setNewUser({ username: '', email: '', password: '', role: 'ROLE_USER' })
            fetchUsers()
        } catch (error: any) {
            toast.error(error.message || 'Échec de la création')
        }
    }

    const columns = [
        {
            key: 'username' as keyof User,
            label: 'Utilisateur',
            render: (value: any, row: User) => (
                <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${row.role === 'ROLE_ADMIN' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                        {row.role === 'ROLE_ADMIN' ? <Shield size={14} /> : <UserIcon size={14} />}
                    </div>
                    <div>
                        <div className="font-medium text-foreground">{row.username}</div>
                        <div className="text-xs text-muted-foreground">{row.email || 'Pas d\'email'}</div>
                    </div>
                </div>
            )
        },
        {
            key: 'role' as keyof User,
            label: 'Rôle',
            render: (value: any) => (
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${value === 'ROLE_ADMIN' ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-blue-100 text-blue-700 border border-blue-200'
                    }`}>
                    {value === 'ROLE_ADMIN' ? 'ADMINISTRATEUR' : 'ANALYSTE'}
                </span>
            )
        },
        {
            key: 'is_active' as keyof User,
            label: 'Statut',
            render: (value: any) => (
                <div className="flex items-center gap-2">
                    {value ? (
                        <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
                            <CheckCircle2 size={14} /> Actif
                        </span>
                    ) : (
                        <span className="flex items-center gap-1 text-red-500 text-xs font-medium">
                            <XCircle size={14} /> Inactif
                        </span>
                    )}
                </div>
            )
        },
        {
            key: 'last_login' as keyof User,
            label: 'Dernier Login',
            render: (value: any) => value ? new Date(value).toLocaleString() : 'Jamais'
        }
    ]

    const actions = (row: User) => (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                    <MoreVertical size={16} />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => toggleUserStatus(row)}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    <span>{row.is_active ? 'Désactiver' : 'Activer'}</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => resetPassword(row.username)}>
                    <Lock className="mr-2 h-4 w-4" />
                    <span>Réinitialiser MDP</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => deleteUser(row.username)}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    <span>Supprimer</span>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )

    if (!isAdmin) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
                <Shield size={48} className="text-destructive animate-pulse" />
                <h1 className="text-2xl font-bold">Accès Non Autorisé</h1>
                <p className="text-muted-foreground">Vous n'avez pas les privilèges nécessaires pour accéder à cette page.</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Gestion des Utilisateurs</h1>
                    <p className="text-muted-foreground">Administrez les accès et les rôles de la plateforme.</p>
                </div>
                <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
                    <DialogTrigger asChild>
                        <Button className="gap-2">
                            <UserPlus size={18} />
                            Nouvel Utilisateur
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <form onSubmit={handleCreateUser}>
                            <DialogHeader>
                                <DialogTitle>Ajouter un Utilisateur</DialogTitle>
                                <DialogDescription>
                                    Créez un nouvel accès pour un analyste ou un administrateur.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="username">Nom d'utilisateur</Label>
                                    <Input
                                        id="username"
                                        value={newUser.username}
                                        onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={newUser.email}
                                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="password">Mot de passe provisoire</Label>
                                    <Input
                                        id="password"
                                        type="password"
                                        value={newUser.password}
                                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="role">Rôle</Label>
                                    <Select
                                        value={newUser.role}
                                        onValueChange={(val) => setNewUser({ ...newUser, role: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Sélectionner un rôle" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="ROLE_USER">Analyste (Lecture/IA)</SelectItem>
                                            <SelectItem value="ROLE_ADMIN">Administrateur (Complet)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="button" variant="outline" onClick={() => setIsAddUserOpen(false)}>Annuler</Button>
                                <Button type="submit">Créer le compte</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                    <form onSubmit={handleSearch} className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                        <Input
                            placeholder="Rechercher par nom ou email..."
                            className="pl-10"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </form>
                    <div className="flex gap-2">
                        <select
                            className="bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            value={roleFilter}
                            onChange={(e) => setRoleFilter(e.target.value)}
                        >
                            <option value="all">Tous les rôles</option>
                            <option value="ROLE_ADMIN">Admin</option>
                            <option value="ROLE_USER">Analyste</option>
                        </select>
                        <Button variant="outline" size="icon">
                            <Filter size={18} />
                        </Button>
                    </div>
                </div>

                <DataTable
                    columns={columns}
                    data={users}
                    rowKey="username"
                    actions={actions}
                />

                <div className="mt-4 flex items-center justify-between py-2">
                    <div className="text-sm text-muted-foreground">
                        Affichage de {users.length} utilisateur(s)
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" disabled>Précédent</Button>
                        <Button variant="outline" size="sm" disabled>Suivant</Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
