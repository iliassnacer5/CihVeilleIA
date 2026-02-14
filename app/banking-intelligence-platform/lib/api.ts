// ==============================================
// API Configuration & Utilities
// ==============================================

// Get API base URL from environment with fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10);

const AUTH_TOKEN_KEY = 'cih_veille_auth_token';

// Helper to manage auth token
export const auth = {
    getToken: () => typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null,
    setToken: (token: string) => typeof window !== 'undefined' ? localStorage.setItem(AUTH_TOKEN_KEY, token) : null,
    clearToken: () => typeof window !== 'undefined' ? localStorage.removeItem(AUTH_TOKEN_KEY) : null,
};

// ==============================================
// Error Types & Logging
// ==============================================

export enum ApiErrorType {
    NETWORK = 'NETWORK_ERROR',
    TIMEOUT = 'TIMEOUT_ERROR',
    HTTP = 'HTTP_ERROR',
    PARSE = 'PARSE_ERROR',
    UNKNOWN = 'UNKNOWN_ERROR'
}

export class ApiError extends Error {
    constructor(
        public type: ApiErrorType,
        public message: string,
        public statusCode?: number,
        public originalError?: Error
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

function logApiError(error: ApiError, path: string) {
    const timestamp = new Date().toISOString();
    console.group(`🚨 API Error [${timestamp}]`);
    console.error('Path:', path);
    console.error('Type:', error.type);
    console.error('Message:', error.message);
    if (error.statusCode) console.error('Status:', error.statusCode);
    if (error.originalError) console.error('Original:', error.originalError);
    console.groupEnd();
}

// ==============================================
// Enhanced Fetch with Timeout & Retry
// ==============================================

export async function fetchWithTimeout(
    resource: string,
    options: RequestInit = {},
    timeout: number = DEFAULT_TIMEOUT
): Promise<any> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    // Ensure resource starts with /
    const path = resource.startsWith('/') ? resource : `/${resource}`;
    const url = `${API_BASE_URL}${path}`;

    // Get auth token if available
    const token = auth.getToken();

    // Prepare headers
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        console.log(`📡 API Request: ${url}`);

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers,
        });

        clearTimeout(id);

        // Handle 401 Unauthorized globally
        if (response.status === 401 && path !== '/token') {
            console.warn('⚠️ Unauthorized access detected, clearing session...');
            auth.clearToken();
            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }
            throw new ApiError(ApiErrorType.HTTP, 'Session expired. Please log in again.', 401);
        }

        // Handle non-OK responses
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

            try {
                const errorData = await response.json();
                if (errorData && errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch {
                // Unable to parse JSON error body, try text
                try {
                    const textError = await response.text();
                    if (textError) errorMessage = textError;
                } catch {
                    // Fallback to default message
                }
            }

            const error = new ApiError(
                ApiErrorType.HTTP,
                errorMessage,
                response.status
            );
            logApiError(error, path);
            throw error;
        }

        // Parse JSON response
        try {
            const data = await response.json();
            console.log(`✅ API Success: ${path}`, data);
            return data;
        } catch (parseError) {
            const error = new ApiError(
                ApiErrorType.PARSE,
                'Failed to parse JSON response',
                response.status,
                parseError as Error
            );
            logApiError(error, path);
            throw error;
        }

    } catch (error: any) {
        clearTimeout(id);

        // Handle abort (timeout)
        if (error.name === 'AbortError') {
            const timeoutError = new ApiError(
                ApiErrorType.TIMEOUT,
                `Request timeout after ${timeout}ms`,
                undefined,
                error
            );
            logApiError(timeoutError, path);
            throw timeoutError;
        }

        // Handle network errors
        if (error instanceof TypeError || error.message?.includes('fetch')) {
            const networkError = new ApiError(
                ApiErrorType.NETWORK,
                'Network error - Backend might be offline. Please check if the server is running.',
                undefined,
                error
            );
            logApiError(networkError, path);
            throw networkError;
        }

        // Re-throw ApiError instances
        if (error instanceof ApiError) {
            throw error;
        }

        // Unknown error
        const unknownError = new ApiError(
            ApiErrorType.UNKNOWN,
            error.message || 'An unknown error occurred',
            undefined,
            error
        );
        logApiError(unknownError, path);
        throw unknownError;
    }
}

// ==============================================
// Retry Logic Wrapper
// ==============================================

export async function fetchWithRetry(
    resource: string,
    options: RequestInit = {},
    maxRetries: number = 2,
    timeout: number = DEFAULT_TIMEOUT
): Promise<any> {
    let lastError: ApiError | undefined;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            if (attempt > 0) {
                console.log(`🔄 Retry attempt ${attempt}/${maxRetries} for ${resource}`);
                // Exponential backoff: 1s, 2s, 4s...
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt - 1) * 1000));
            }

            return await fetchWithTimeout(resource, options, timeout);
        } catch (error) {
            lastError = error as ApiError;

            // Don't retry on HTTP 4xx errors (client errors)
            if (lastError.statusCode && lastError.statusCode >= 400 && lastError.statusCode < 500) {
                throw lastError;
            }

            // Don't retry on the last attempt
            if (attempt === maxRetries) {
                throw lastError;
            }
        }
    }

    throw lastError!;
}

// ==============================================
// TypeScript Interfaces
// ==============================================

export interface User {
    id?: string;
    username: string;
    email?: string;
    role: string;
    is_active: boolean;
    last_login?: string;
    created_at?: string;
}

export interface AuditLog {
    id?: string;
    timestamp: number;
    user_id: string;
    username: string;
    role: string;
    action: string;
    module: string;
    status: string;
    details?: any;
    ip_address?: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
}

export interface Source {
    id: string;
    name: string;
    url: string;
    type: string;
    frequency: string;
    status: string;
    lastUpdated: string;
    whitelisted: boolean;
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

// ==============================================
// API Methods
// ==============================================

export const api = {
    // Auth Methods
    login: async (username: string, password: string): Promise<AuthResponse> => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const data = await fetchWithTimeout('/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        auth.setToken(data.access_token);
        return data;
    },

    getCurrentUser: (): Promise<User> => fetchWithRetry('/users/me'),

    logout: () => {
        auth.clearToken();
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
    },

    isAuthenticated: () => !!auth.getToken(),

    // Health Check
    healthCheck: () => fetchWithTimeout('/health'),

    // Sources
    getSources: (): Promise<Source[]> => fetchWithRetry('/sources'),
    addSource: (source: { name: string; url: string; type: string; frequency: string }): Promise<Source> =>
        fetchWithRetry('/sources', {
            method: 'POST',
            body: JSON.stringify(source),
        }),
    scrapeSource: (sourceId: string) => fetchWithRetry(`/sources/scrape/${sourceId}`, {}, 0, 300000),
    deleteSource: (sourceId: string) => fetchWithRetry(`/sources/${sourceId}`, { method: 'DELETE' }),

    // Analytics
    getKpis: (): Promise<KpiResponse> => fetchWithRetry('/analytics/kpis'),
    getDashboardAnalytics: (): Promise<DashboardAnalytics> => fetchWithRetry('/analytics/dashboard'),

    // Documents
    getDocuments: (): Promise<Document[]> => fetchWithRetry('/documents'),
    getDocumentDetail: (docId: string) => fetchWithRetry(`/documents/${docId}`),
    deleteDocument: (docId: string) => fetchWithTimeout(`/documents/${docId}`, { method: 'DELETE' }),
    bulkDeleteDocuments: (docIds: string[]) => fetchWithTimeout('/documents/bulk-delete', {
        method: 'POST',
        body: JSON.stringify({ doc_ids: docIds }),
    }),
    summarizeDocument: (docId: string): Promise<SummarizeResponse> =>
        fetchWithRetry(`/documents/${docId}/summarize`, { method: 'POST' }, 1, 300000), // 5min timeout for AI processing
    uploadDocument: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const token = auth.getToken();
        const headers: Record<string, string> = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return fetch(`${API_BASE_URL}/documents/upload`, {
            method: 'POST',
            headers,
            body: formData,
        }).then(res => res.json());
    },

    // Search & Chat
    search: (question: string) => fetchWithRetry('/search', {
        method: 'POST',
        body: JSON.stringify({ question }),
    }),
    askChatbot: (question: string) => fetchWithRetry('/chatbot/ask', {
        method: 'POST',
        body: JSON.stringify({ question }),
    }),

    // Alerts
    getLatestAlerts: (): Promise<Alert[]> => fetchWithRetry('/alerts/latest'),
    getUnreadAlertsCount: (): Promise<{ count: number }> => fetchWithRetry('/alerts/unread-count'),
    markAlertAsRead: (alertId: string): Promise<any> => fetchWithRetry(`/alerts/${alertId}/read`, { method: 'POST' }),

    // Translation
    translateDocument: (docId: string): Promise<{ translated_text: string; original_lang: string; target_lang: string }> =>
        fetchWithRetry(`/documents/${docId}/translate`, { method: 'POST' }),

    // Scheduler Controls
    getSchedulerStatus: (): Promise<any> => fetchWithRetry('/scheduler/status'),
    startScheduler: () => fetchWithRetry('/scheduler/start', { method: 'POST' }),
    stopScheduler: () => fetchWithRetry('/scheduler/stop', { method: 'POST' }),
    scrapeAllSources: () => fetchWithRetry('/scrape-all', { method: 'POST' }, 0, 600000), // 10min timeout

    // Audit & Settings
    getAuditLogs: () => fetchWithRetry('/audit/logs'),
    getSettings: () => fetchWithRetry('/settings'),
    updateSettings: (settings: any) => fetchWithRetry('/settings', {
        method: 'POST',
        body: JSON.stringify(settings),
    }),
    getWhitelistedDomains: () => fetchWithRetry('/settings/domains'),
    addWhitelistedDomain: (domain: any) => fetchWithRetry('/settings/domains', {
        method: 'POST',
        body: JSON.stringify(domain),
    }),

    // Generic Methods
    get: (url: string, options: any = {}) => {
        let fullUrl = url;
        if (options.params) {
            const params = new URLSearchParams();
            Object.entries(options.params).forEach(([key, value]) => {
                if (value !== undefined) params.append(key, String(value));
            });
            fullUrl += `?${params.toString()}`;
        }
        return fetchWithRetry(fullUrl, options);
    },
    post: (url: string, body: any) => fetchWithRetry(url, {
        method: 'POST',
        body: JSON.stringify(body),
    }),
    patch: (url: string, body: any) => fetchWithRetry(url, {
        method: 'PATCH',
        body: JSON.stringify(body),
    }),
    delete: (url: string) => fetchWithRetry(url, { method: 'DELETE' }),
};
