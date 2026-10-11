import type { HealthResponse, ApiErrorResponse } from '../types';


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
    let errorData: ApiErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // Non-json response
    }

    const message =
      errorData?.error?.message ||
      `Request failed with status ${response.status} (${response.statusText})`;
    const code = errorData?.error?.code || `HTTP_${response.status}`;
    const details = errorData?.error?.details || [];

    throw new ApiClientError(message, code, details);
  }

  return response.json();
}

export const api = {
  getHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/health'),
  getApiHealth: (): Promise<HealthResponse> => apiRequest<HealthResponse>('/api/health'),
  getRootStatus: (): Promise<{ app: string; status: string }> => apiRequest('/'),
};
