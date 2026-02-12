'use client';

import { useEffect, useRef } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { Bell, Info, ExternalLink } from 'lucide-react';

export function RealTimeNotifications() {
    const { user } = useAuth();
    const { toast } = useToast();
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!user) {
            if (socketRef.current) {
                socketRef.current.close();
                socketRef.current = null;
            }
            return;
        }

        const API_BASE_WS = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000';
        const wsUrl = `${API_BASE_WS}/ws/notifications/${user.username}`;

        console.log(`🔌 Initializing WebSocket connection to: ${wsUrl}`);
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
            console.log('✅ WebSocket Connected');
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('📨 WebSocket Message Received:', message);

                if (message.type === 'new_document_alert') {
                    const alert = message.data;
                    const metadata = alert.metadata || {};

                    toast({
                        title: alert.title || 'Nouveau document ajouté',
                        description: (
                            <div className="mt-2 space-y-1">
                                <p className="text-sm font-medium">{alert.message}</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                    <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[10px] font-bold uppercase">
                                        {metadata.doc_type || 'DOC'}
                                    </span>
                                    <span className="bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded text-[10px] font-bold uppercase">
                                        {metadata.source || 'Unknown'}
                                    </span>
                                </div>
                                <div className="pt-2 flex items-center justify-between">
                                    <span className="text-[10px] opacity-70 italic">{metadata.added_at}</span>
                                    {metadata.url && (
                                        <a
                                            href={metadata.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline flex items-center gap-1 text-[10px] font-bold"
                                        >
                                            Voir <ExternalLink size={10} />
                                        </a>
                                    )}
                                </div>
                            </div>
                        ),
                        duration: 8000,
                    });
                }
            } catch (err) {
                console.error('❌ Error parsing WebSocket message:', err);
            }
        };

        socket.onclose = (event) => {
            console.log('🔌 WebSocket Disconnected', event.reason);
            // Optional: auto-reconnect logic
            if (user) {
                setTimeout(() => {
                    // Check if user is still logged in before reconnecting
                }, 5000);
            }
        };

        socket.onerror = (error) => {
            console.error('❌ WebSocket Error:', error);
        };

        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, [user, toast]);

    return null; // Component only handles side effects
}
