import type { HealthResponse } from '../types';
import type {
  AIInsightResponse,
  AuthTokenResponse,
  AuthUser,
  Trial,
  TrialListResponse,
  TrialMetricsResponse,
} from '../types/trials';

export interface CsvPreviewRow {
  participant_id: string;
  status: string;
  visits_completed?: number | null;
  visits_planned?: number | null;
  enrollment_date?: string | null;
  last_visit_date?: string | null;
  next_visit_due_date?: string | null;
}

export interface CsvPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: string[];
  preview: CsvPreviewRow[];
}

export interface DatasetProfile {
  file_name: string;
  row_count: number;
  column_count: number;
  original_headers: string[];
  normalized_headers: string[];
  inferred_types: Record<string, string>;
  missing_counts: Record<string, number>;
  samples: Record<string, string[]>;
}

export interface DatasetClassification {
  type: string;
  confidence: number;
  evidence: string[];
  proposed_mappings: Record<string, string[]>;
}

export interface DatasetPreviewResponse {
  profile: DatasetProfile;
  classification: DatasetClassification;
  participant_preview?: CsvPreviewResponse | null;
}

export interface CsvImportResponse {
  trial_id: string;
  imported_count: number;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: string[];
  preview: CsvPreviewRow[];
}

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

let accessToken: string | null = null;
let currentUser: AuthUser | null = null;
let refreshPromise: Promise<string> | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (!token) {
    currentUser = null;
  }
}

export function setCurrentUser(user: AuthUser | null): void {
  currentUser = user;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getCurrentUser(): AuthUser | null {
  return currentUser;
}

export function clearSession(): void {
  accessToken = null;
  currentUser = null;
  refreshPromise = null;
}

export class ApiClientError extends Error {
  code: string;
  details: string[];

  constructor(message: string, code = 'API_ERROR', details: string[] = []) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.details = details;
  }
}

function normalizeApiError(errorData: unknown, status: number, statusText: string): {
  message: string;
  code: string;
  details: string[];
} {
  const fallback = {
    message: `Request failed with status ${status} (${statusText})`,
    code: `HTTP_${status}`,
    details: [] as string[],
  };

  if (!errorData || typeof errorData !== 'object') {
    return fallback;
  }

  const candidate =
    'error' in errorData && errorData.error && typeof errorData.error === 'object'
      ? errorData.error
      : 'detail' in errorData && errorData.detail && typeof errorData.detail === 'object'
        ? errorData.detail
        : errorData;

  if (!candidate || typeof candidate !== 'object') {
    return fallback;
  }

  const payload = candidate as Record<string, unknown>;
  const message =
    typeof payload.message === 'string'
      ? payload.message
      : typeof payload.error === 'string'
        ? payload.error
        : fallback.message;
  const code = typeof payload.code === 'string' ? payload.code : fallback.code;
  const details =
    Array.isArray(payload.details) && payload.details.every((item) => typeof item === 'string')
      ? payload.details
      : [];

  return { message, code, details };
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        let errorData: unknown = null;
        try {
          errorData = await response.json();
        } catch {
          // Non-json response
        }

        const { message } = normalizeApiError(errorData, response.status, response.statusText);
        throw new ApiClientError(message, `HTTP_${response.status}`);
      }

      const data = (await response.json()) as AuthTokenResponse;
      setAccessToken(data.access_token);
      setCurrentUser(data.user);
      return data.access_token;
    })();
  }

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit & { __retry?: boolean } = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const executeRequest = async (isRetry: boolean): Promise<T> => {
    const defaultHeaders: Record<string, string> = {
      Accept: 'application/json',
    };

    if (!(options.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    const headerEntries = new Headers(options.headers ?? undefined);
    const hasAuthorizationHeader =
      headerEntries.has('Authorization') ||
      Array.isArray(options.headers) && options.headers.some(([key]) => key.toLowerCase() === 'authorization');

    if (accessToken && !hasAuthorizationHeader) {
      defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
    }

    const mergedHeaders = new Headers(defaultHeaders);
    if (options.headers) {
      const providedHeaders = new Headers(options.headers);
      for (const [key, value] of providedHeaders.entries()) {
        mergedHeaders.set(key, value);
      }
    }

    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: mergedHeaders,
    });

    const canRefresh =
      !isRetry &&
      !endpoint.includes('/api/auth/login') &&
      !endpoint.includes('/api/auth/register') &&
      !endpoint.includes('/api/auth/refresh');

    if (response.status === 401 && canRefresh) {
      try {
        await refreshAccessToken();
        return executeRequest(true);
      } catch {
        clearSession();
        throw new ApiClientError('Your session expired. Please sign in again.', 'HTTP_401');
      }
    }

    if (!response.ok) {
      let errorData: unknown = null;
      try {
        errorData = await response.json();
      } catch {
        // Non-json response
      }

      const { message, code, details } = normalizeApiError(errorData, response.status, response.statusText);
      throw new ApiClientError(message, code, details);
    }

    return response.json();
  };

  return executeRequest(Boolean(options.__retry));
}

export const api = {
  getHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/health'),
  getApiHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/api/health'),
  getRootStatus: (): Promise<{ app: string; status: string }> => apiRequest('/'),
  register: async (email: string, password: string): Promise<AuthTokenResponse> => {
    const response = await apiRequest<AuthTokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(response.access_token);
    setCurrentUser(response.user);
    return response;
  },
  login: async (email: string, password: string): Promise<AuthTokenResponse> => {
    const response = await apiRequest<AuthTokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(response.access_token);
    setCurrentUser(response.user);
    return response;
  },
  logout: async (): Promise<void> => {
    try {
      await apiRequest('/api/auth/logout', { method: 'POST' });
    } finally {
      clearSession();
    }
  },
  getTrials: (token?: string): Promise<TrialListResponse> =>
    apiRequest<TrialListResponse>('/api/trials', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }),
  createTrial: (
    token: string,
    payload: {
      trial_code: string;
      trial_name: string;
      status: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<Trial> =>
    apiRequest<Trial>('/api/trials', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    }),
  previewParticipants: (trialId: string, file: File): Promise<CsvPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest<CsvPreviewResponse>(`/api/trials/${trialId}/participants/preview`, {
      method: 'POST',
      body: formData,
    });
  },
  previewDataset: (trialId: string, file: File): Promise<DatasetPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest<DatasetPreviewResponse>(`/api/trials/${trialId}/datasets/preview`, {
      method: 'POST',
      body: formData,
    });
  },
  importParticipants: (trialId: string, file: File, confirmed = true): Promise<CsvImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('confirm', String(confirmed));

    return apiRequest<CsvImportResponse>(`/api/trials/${trialId}/participants/import`, {
      method: 'POST',
      body: formData,
    });
  },
  getTrialMetrics: (trialId: string, token?: string): Promise<TrialMetricsResponse> =>
    apiRequest<TrialMetricsResponse>(`/api/trials/${trialId}/metrics`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }),
  generateTrialInsights: (
    trialId: string,
    topic: 'enrollment' | 'completion' | 'withdrawals' | 'participant_status_distribution',
    token?: string
  ): Promise<AIInsightResponse> =>
    apiRequest<AIInsightResponse>(`/api/trials/${trialId}/ai-analysis`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: JSON.stringify({ topic }),
    }),
  getAccessToken,
  getCurrentUser,
  setAccessToken,
  setCurrentUser,
  clearSession,
};
