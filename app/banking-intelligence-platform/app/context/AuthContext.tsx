'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api, User } from '@/lib/api';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    isAdmin: boolean;
    isUser: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const checkAuth = async () => {
            if (api.isAuthenticated()) {
                try {
                    const currentUser = await api.getCurrentUser();
                    setUser(currentUser);
                } catch (error) {
                    console.error('Failed to fetch current user:', error);
                    api.logout(); // Clears token and redirects
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    const login = async (username: string, password: string) => {
        setIsLoading(true);
        try {
            await api.login(username, password);
            const currentUser = await api.getCurrentUser();
            setUser(currentUser);
            router.push('/');
        } catch (error) {
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        setUser(null);
        api.logout();
    };

    // Protection logic - simplified for layout usage
    useEffect(() => {
        if (!isLoading && !user && pathname !== '/login') {
            router.push('/login');
        }
    }, [user, isLoading, pathname, router]);

    const isAdmin = user?.role === 'ROLE_ADMIN';
    const isUser = user?.role === 'ROLE_USER';

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout, isAuthenticated: !!user, isAdmin, isUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
