import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, BarChart3, CheckCircle2, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Trial, TrialMetricsResponse } from '../types/trials';

const statusColors: Record<string, string> = {
  completed: '#10b981',
  withdrawn: '#f59e0b',
  active: '#38bdf8',
};

export const MetricsPage: React.FC = () => {
  const token = useMemo(() => localStorage.getItem('access_token'), []);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [selectedTrialId, setSelectedTrialId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<TrialMetricsResponse | null>(null);
  const [loadingTrials, setLoadingTrials] = useState<boolean>(false);
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setTrials([]);
      setMetrics(null);
      setSelectedTrialId(null);
      return;
    }

    const loadTrials = async () => {
      try {
        setLoadingTrials(true);
        setError(null);
        const data = await api.getTrials(token);
        setTrials(data.trials);
        if (data.trials.length > 0 && !selectedTrialId) {
          setSelectedTrialId(data.trials[0].id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Unable to load trial data.');
      } finally {
        setLoadingTrials(false);
      }
    };

    void loadTrials();
  }, [selectedTrialId, token]);

  useEffect(() => {
    if (!selectedTrialId || !token) {
      setMetrics(null);
      return;
    }

    const loadMetrics = async () => {
      try {
        setLoadingMetrics(true);
        setError(null);
        const data = await api.getTrialMetrics(selectedTrialId, token);
        setMetrics(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Unable to load trial metrics.');
      } finally {
        setLoadingMetrics(false);
      }
    };

    void loadMetrics();
  }, [selectedTrialId, token]);

  const chartData = metrics?.status_breakdown ?? [];
  const maxCount = Math.max(1, ...chartData.map((item) => item.count));

  if (!token) {
    return (
      <div className="card" style={{ maxWidth: 640 }}>
        <div className="card-header">
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Phase 4
            </div>
            <h2 className="card-title">Trial Metrics</h2>
          </div>
        </div>
        <div style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
          Please sign in to access the trial metrics dashboard.
        </div>
        <div style={{ marginTop: '1rem' }}>
          <Link to="/trials" className="btn btn-primary">
            <span>Open trial access</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  if (loadingTrials) {
    return (
      <div className="card" style={{ maxWidth: 560 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
          <Loader2 size={16} className="spin" />
          Loading trials and metrics...
        </div>
      </div>
    );
  }

  if (!trials.length) {
    return (
      <div className="card" style={{ maxWidth: 640 }}>
        <div className="card-header">
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Phase 4
            </div>
            <h2 className="card-title">Trial Metrics</h2>
          </div>
        </div>

        <div style={{ marginTop: '1.25rem', color: 'var(--text-secondary)' }}>
          No trials are available yet. Create a trial to begin tracking participant status metrics.
        </div>
        <div style={{ marginTop: '1rem' }}>
          <Link to="/trials" className="btn btn-primary">
            <span>Create a trial</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: '1.5rem' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Phase 4
            </div>
            <h2 className="card-title">Trial Metrics Dashboard</h2>
          </div>
          <label style={{ display: 'grid', gap: '0.35rem', minWidth: 220 }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Selected trial</span>
            <select
              value={selectedTrialId ?? trials[0].id}
              onChange={(event) => setSelectedTrialId(event.target.value)}
              style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              aria-label="Select trial for metrics"
            >
              {trials.map((trial) => (
                <option key={trial.id} value={trial.id}>
                  {trial.trial_code} — {trial.trial_name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {error ? (
          <div style={{ marginTop: '1rem', padding: '0.9rem 1rem', borderRadius: '0.5rem', background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.3)', color: 'var(--accent-rose)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
              <AlertTriangle size={16} />
              Metrics unavailable
            </div>
            <div style={{ marginTop: '0.4rem' }}>{error}</div>
          </div>
        ) : null}

        {loadingMetrics && !metrics ? (
          <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
            <Loader2 size={16} className="spin" />
            Calculating status metrics...
          </div>
        ) : null}
      </div>

      {metrics ? (
        <>
          <div className="grid-3">
            {[
              { label: 'Total participants', value: metrics.total_participants, hint: 'All imported records' },
              { label: 'Completed', value: metrics.completed_count, hint: `${metrics.completion_rate.toFixed(2)}%` },
              { label: 'Withdrawn', value: metrics.withdrawn_count, hint: `${metrics.withdrawal_rate.toFixed(2)}%` },
              { label: 'Active', value: metrics.active_count, hint: `${metrics.active_rate.toFixed(2)}%` },
              { label: 'Completion rate', value: `${metrics.completion_rate.toFixed(2)}%`, hint: 'completed_count / total_participants * 100' },
              { label: 'Withdrawal rate', value: `${metrics.withdrawal_rate.toFixed(2)}%`, hint: 'withdrawn_count / total_participants * 100' },
            ].map((card) => (
              <div key={card.label} className="metric-card">
                <div className="metric-label">{card.label}</div>
                <div className="metric-value">{card.value}</div>
                <div className="metric-sub">{card.hint}</div>
              </div>
            ))}
          </div>

          {metrics.empty_trial ? (
            <div className="card" style={{ borderColor: 'rgba(14, 165, 233, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                <BarChart3 size={18} />
                Empty trial state
              </div>
              <div style={{ marginTop: '0.75rem', color: 'var(--text-secondary)' }}>
                {metrics.summary}
              </div>
            </div>
          ) : (
            <div className="grid-2">
              <div className="card">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Status breakdown</h3>
                    <div className="card-subtitle">Counts and percentages for all supported statuses</div>
                  </div>
                </div>

                <div style={{ marginTop: '1.25rem', display: 'grid', gap: '1rem' }}>
                  {chartData.map((item) => (
                    <div key={item.status} aria-label={`${item.label}: ${item.count} participants, ${item.rate.toFixed(2)} percent`}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.45rem', color: 'var(--text-secondary)' }}>
                        <strong style={{ color: 'var(--text-primary)' }}>{item.label}</strong>
                        <span>
                          {item.count} ({item.rate.toFixed(2)}%)
                        </span>
                      </div>
                      <div style={{ height: '12px', borderRadius: '999px', background: 'rgba(148, 163, 184, 0.18)', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${Math.max(4, (item.count / maxCount) * 100)}%`,
                            background: statusColors[item.status] ?? 'var(--accent-primary)',
                            borderRadius: 'inherit',
                          }}
                        />
                      </div>
                      <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {item.summary}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Summary</h3>
                    <div className="card-subtitle">Readable narrative for the status mix</div>
                  </div>
                </div>

                <p style={{ marginTop: '1rem', fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
                  {metrics.summary}
                </p>

                <div style={{ marginTop: '1.25rem', display: 'grid', gap: '0.75rem' }}>
                  {metrics.data_quality.warning ? (
                    <div style={{ padding: '0.8rem 0.9rem', borderRadius: '0.5rem', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', color: 'var(--accent-amber)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                        <AlertTriangle size={16} />
                        Data quality warning
                      </div>
                      <div style={{ marginTop: '0.4rem' }}>{metrics.data_quality.warning}</div>
                    </div>
                  ) : (
                    <div style={{ padding: '0.8rem 0.9rem', borderRadius: '0.5rem', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', color: 'var(--accent-emerald)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                        <CheckCircle2 size={16} />
                        Status counts reconcile
                      </div>
                    </div>
                  )}

                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    Calculation method: {metrics.calculation_method} • AI generated: {metrics.ai_generated ? 'yes' : 'no'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
};
