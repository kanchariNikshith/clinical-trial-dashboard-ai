import type { HealthResponse } from '../types';
import type {
  AIInsightResponse,
  AuthTokenResponse,
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

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: Record<string, string> = {
    Accept: 'application/json',
  };

  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const token = localStorage.getItem('access_token');
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

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
}

export const api = {
  getHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/health'),
  getApiHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/api/health'),
  getRootStatus: (): Promise<{ app: string; status: string }> => apiRequest('/'),
  register: (email: string, password: string): Promise<AuthTokenResponse> =>
    apiRequest<AuthTokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string): Promise<AuthTokenResponse> =>
    apiRequest<AuthTokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
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
};
