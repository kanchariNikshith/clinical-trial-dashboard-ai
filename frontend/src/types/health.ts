export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: string[];
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
