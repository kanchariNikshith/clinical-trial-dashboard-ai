import { useEffect, useState, type FormEvent } from 'react';

import { api } from '../api/client';
import type { Trial, AIInsightResponse } from '../types/trials';

const ANALYSIS_TOPICS = [
  { value: 'enrollment', label: 'Enrollment' },
  { value: 'completion', label: 'Completion' },
  { value: 'withdrawals', label: 'Withdrawals' },
  { value: 'participant_status_distribution', label: 'Participant status distribution' },
] as const;

export function AIInsightsPage() {
  const [trials, setTrials] = useState<Trial[]>([]);
  const [selectedTrialId, setSelectedTrialId] = useState<string>('');
  const [selectedTopic, setSelectedTopic] = useState<(typeof ANALYSIS_TOPICS)[number]['value']>('enrollment');
  const [result, setResult] = useState<AIInsightResponse | null>(null);
  const [loadingTrials, setLoadingTrials] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTrials = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setTrials([]);
        setSelectedTrialId('');
        return;
      }

      try {
        setLoadingTrials(true);
        const data = await api.getTrials(token);
        setTrials(data.trials);
        if (data.trials.length > 0) {
          setSelectedTrialId((current) => current || data.trials[0].id);
        }
      } catch {
        setError('Unable to load the available trials.');
      } finally {
        setLoadingTrials(false);
      }
    };

    void loadTrials();
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const token = localStorage.getItem('access_token');

    if (!selectedTrialId || !token) {
      setError('Please sign in and choose a trial before generating an insight.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const payload = await api.generateTrialInsights(selectedTrialId, selectedTopic, token);
      setResult(payload);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Unable to generate the AI summary.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' }}>
      <h1>AI Insights</h1>
      <p>
        Generate an aggregate-only operational summary. The output is advisory and requires human review.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem', marginTop: '1.5rem' }}>
        <label style={{ display: 'grid', gap: '0.5rem' }}>
          <span>Trial</span>
          <select
            value={selectedTrialId}
            onChange={(event) => setSelectedTrialId(event.target.value)}
            disabled={loadingTrials || trials.length === 0}
          >
            {trials.length === 0 ? (
              <option value="">No trials available</option>
            ) : (
              trials.map((trial) => (
                <option key={trial.id} value={trial.id}>
                  {trial.trial_name} ({trial.trial_code})
                </option>
              ))
            )}
          </select>
        </label>

        <label style={{ display: 'grid', gap: '0.5rem' }}>
          <span>Operational topic</span>
          <select
            value={selectedTopic}
            onChange={(event) => setSelectedTopic(event.target.value as (typeof ANALYSIS_TOPICS)[number]['value'])}
            aria-label="AI analysis topic"
          >
            {ANALYSIS_TOPICS.map((topic) => (
              <option key={topic.value} value={topic.value}>
                {topic.label}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={submitting || !selectedTrialId}>
          {submitting ? 'Generating insight...' : 'Generate AI insight'}
        </button>
      </form>

      {error ? (
        <div style={{ marginTop: '1.5rem', padding: '1rem', border: '1px solid #d32f2f', borderRadius: 8 }}>
          <strong>Insight unavailable.</strong>
          <div>{error}</div>
        </div>
      ) : null}

      {result ? (
        <section style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #d0d7de', borderRadius: 12 }}>
          <div style={{ fontSize: '0.85rem', color: '#57606a', marginBottom: '0.75rem' }}>
            AI-generated using {result.model} on {new Date(result.generated_at).toLocaleString()}
          </div>
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{result.analysis}</div>
          <div style={{ marginTop: '1rem', fontStyle: 'italic', color: '#57606a' }}>{result.disclaimer}</div>
        </section>
      ) : null}
    </div>
  );
}
