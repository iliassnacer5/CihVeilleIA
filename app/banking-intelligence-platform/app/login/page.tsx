'use client';

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, Lock, User, AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const { login, isLoading } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!username || !password) {
            setError('Veuillez remplir tous les champs.');
            return;
        }

        try {
            await login(username, password);
        } catch (err: any) {
            console.error('Login error:', err);
            setError(err.message || 'Identifiants invalides ou erreur serveur.');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#f0f2f5] p-4 relative overflow-hidden">
            {/* Background elements for premium feel */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-100 rounded-full blur-3xl opacity-50" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-yellow-50 rounded-full blur-3xl opacity-50" />

            <Card className="w-full max-w-md z-10 border-none shadow-2xl bg-white/80 backdrop-blur-sm">
                <CardHeader className="space-y-1 flex flex-col items-center border-b pb-6">
                    <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center mb-4 shadow-lg">
                        <Globe size={32} className="text-primary-foreground" />
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight text-center">CIH BANK</CardTitle>
                    <CardDescription className="text-center font-medium">
                        Banking Intelligence Platform
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                    <CardContent className="space-y-4 pt-6">
                        {error && (
                            <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2 duration-300">
                                <AlertCircle className="h-4 w-4" />
                                <AlertTitle>Erreur</AlertTitle>
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="username">Utilisateur</Label>
                            <div className="relative">
                                <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="username"
                                    placeholder="admin"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="pl-10"
                                    disabled={isLoading}
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="password">Mot de passe</Label>
                            </div>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="pl-10"
                                    disabled={isLoading}
                                    required
                                />
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-4 pb-8">
                        <Button
                            type="submit"
                            className="w-full h-11 text-base font-semibold transition-all hover:scale-[1.01]"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Connexion en cours...
                                </>
                            ) : (
                                'Se connecter'
                            )}
                        </Button>
                        <p className="text-xs text-center text-muted-foreground px-4">
                            Accès réservé aux analystes autorisés. Toute tentative de connexion non autorisée est enregistrée.
                        </p>
                    </CardFooter>
                </form>
            </Card>

            {/* Corporate branding footer */}
            <div className="absolute bottom-6 left-0 right-0 text-center text-xs text-muted-foreground opacity-60">
                &copy; 2026 CIH Bank - Direction de la Veille et de l'Innovation
            </div>
        </div>
    );
}
