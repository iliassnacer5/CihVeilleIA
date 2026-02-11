const API_BASE_URL = 'http://localhost:8000'; // Hardcoded for local dev as per verify script

export async function fetchWithTimeout(resource: string, options: RequestInit = {}, timeout = 60000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    // Ensure resource starts with /
    const path = resource.startsWith('/') ? resource : `/${resource}`;

    try {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        clearTimeout(id);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error (${response.status}): ${errorText || response.statusText}`);
        }

        return response.json();
    } catch (error) {
        clearTimeout(id);
        console.error(`Fetch error for ${path}:`, error);
        throw error;
    }
}

export interface Source {
    id: string;
    name: string;
    url: string;
    type: string;
    frequency: string;
    status: string;
    lastUpdated: string;
}

export interface KpiResponse {
    monitored_sources: number;
    documents_month: number;
    regulatory_updates: number;
    ai_processing_rate: number;
    avg_processing_time: string;
    system_health: string;
}

export interface DashboardAnalytics {
    documents_over_time: { month: string; documents: number; alerts: number }[];
    distribution_by_theme: { name: string; value: number }[];
}

export interface Alert {
    id: string;
    title: string;
    description: string;
    source: string;
    severity: string;
    category: string;
    timestamp: string;
    read: boolean;
}

export interface Document {
    id: string;
    title: string;
    source: string;
    date: string;
    theme: string;
    confidence: number;
    url?: string;
}

export interface DocumentDetail extends Document {
    summary: string;
    entities: string[];
    content: string;
}

export interface SummarizeResponse {
    id: string;
    summary: string;
    topics: string[];
    entities: string[];
    confidence: number;
    key_facts: string[];
}

export const api = {
    // Sources
    getSources: (): Promise<Source[]> => fetchWithTimeout('/sources'),
    addSource: (source: { name: string; url: string; type: string; frequency: string }): Promise<Source> =>
        fetchWithTimeout('/sources', {
            method: 'POST',
            body: JSON.stringify(source),
        }),
    scrapeSource: (sourceId: string) => fetchWithTimeout(`/sources/scrape/${sourceId}`),
    deleteSource: (sourceId: string) => fetchWithTimeout(`/sources/${sourceId}`, { method: 'DELETE' }),

    // Analytics
    getKpis: (): Promise<KpiResponse> => fetchWithTimeout('/analytics/kpis'),
    getDashboardAnalytics: (): Promise<DashboardAnalytics> => fetchWithTimeout('/analytics/dashboard'),
    getLatestAlerts: (): Promise<Alert[]> => fetchWithTimeout('/alerts/latest'),

    // Documents
    getDocuments: (): Promise<Document[]> => fetchWithTimeout('/documents'),
    getDocumentDetail: (docId: string) => fetchWithTimeout(`/documents/${docId}`),
    summarizeDocument: (docId: string): Promise<SummarizeResponse> => fetchWithTimeout(`/documents/${docId}/summarize`, { method: 'POST' }, 300000),
    uploadDocument: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return fetch(`${API_BASE_URL}/documents/upload`, {
            method: 'POST',
            body: formData,
        }).then(res => res.json());
    },

    // Search & Chat
    search: (question: string) => fetchWithTimeout('/search', {
        method: 'POST',
        body: JSON.stringify({ question }),
    }),
    askChatbot: (question: string) => fetchWithTimeout('/chatbot/ask', {
        method: 'POST',
        body: JSON.stringify({ question }),
    }),

    // Audit & Settings
    getAuditLogs: () => fetchWithTimeout('/audit/logs'),
    getSettings: () => fetchWithTimeout('/settings'),
    updateSettings: (settings: any) => fetchWithTimeout('/settings', {
        method: 'POST',
        body: JSON.stringify(settings),
    }),
    getWhitelistedDomains: () => fetchWithTimeout('/settings/domains'),
    addWhitelistedDomain: (domain: any) => fetchWithTimeout('/settings/domains', {
        method: 'POST',
        body: JSON.stringify(domain),
    }),
};
