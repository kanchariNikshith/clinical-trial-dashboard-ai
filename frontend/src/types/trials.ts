export interface Trial {
  id: string;
  owner_user_id: string;
  trial_code: string;
  trial_name: string;
  status: 'active' | 'paused' | 'completed' | 'cancelled';
  start_date?: string | null;
  end_date?: string | null;
  participant_count: number;
  created_at: string;
  updated_at: string;
}

export interface TrialListResponse {
  trials: Trial[];
  total: number;
}

export interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface StatusBreakdownItem {
  status: string;
  label: string;
  count: number;
  rate: number;
  summary: string;
}

export interface MetricDataQuality {
  status_counts_reconcile: boolean;
  warning?: string | null;
  unsupported_statuses: string[];
}

export interface TrialMetricsResponse {
  trial_id: string;
  total_participants: number;
  completed_count: number;
  withdrawn_count: number;
  active_count: number;
  completion_rate: number;
  withdrawal_rate: number;
  active_rate: number;
  calculation_method: string;
  empty_trial: boolean;
  ai_generated: boolean;
  data_quality: MetricDataQuality;
  definitions: Record<string, string>;
  status_breakdown: StatusBreakdownItem[];
  summary: string;
}

export interface AIInsightResponse {
  analysis: string;
  model: string;
  generated_at: string;
  disclaimer: string;
}
