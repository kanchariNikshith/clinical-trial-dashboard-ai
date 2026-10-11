import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, ClipboardList, Loader2, LogOut, PlusCircle } from 'lucide-react';
import { api } from '../api/client';
import type { AuthTokenResponse, Trial } from '../types/trials';

const emptyForm = {
  trial_code: '',
  trial_name: '',
  status: 'active',
  start_date: '',
  end_date: '',
};

export const TrialsPage: React.FC = () => {
  const storedSession = useMemo(() => {
    const token = api.getAccessToken();
    const user = api.getCurrentUser();
    return token && user ? { token, user } : null;
  }, []);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register');
  const [authForm, setAuthForm] = useState({ email: 'researcher@example.com', password: 'Password123!' });
  const [session, setSession] = useState<{ token: string; user: AuthTokenResponse['user'] } | null>(storedSession);
  const [trialForm, setTrialForm] = useState(emptyForm);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [loadingTrials, setLoadingTrials] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadTrials = async (token: string) => {
    try {
      setLoadingTrials(true);
      setError(null);
      const response = await api.getTrials(token);
      setTrials(response.trials);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to load trials.');
      setTrials([]);
    } finally {
      setLoadingTrials(false);
    }
  };

  useEffect(() => {
    if (!session?.token) {
      setTrials([]);
      return;
    }

    void loadTrials(session.token);
  }, [session?.token]);

  const handleAuthSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response =
        authMode === 'register'
          ? await api.register(authForm.email, authForm.password)
          : await api.login(authForm.email, authForm.password);

      api.setAccessToken(response.access_token);
      api.setCurrentUser(response.user);
      setSession({ token: response.access_token, user: response.user });
      setSuccess(
        authMode === 'register'
          ? 'Account created and trial workspace is ready.'
          : 'Successfully signed in.'
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleCreateTrial = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session?.token) {
      setError('Sign in to create a trial.');
      return;
    }

    setCreating(true);
    setError(null);
    setSuccess(null);

    try {
      await api.createTrial(session.token, {
        trial_code: trialForm.trial_code.trim(),
        trial_name: trialForm.trial_name.trim(),
        status: trialForm.status,
        start_date: trialForm.start_date || undefined,
        end_date: trialForm.end_date || undefined,
      });

      setTrialForm(emptyForm);
      setSuccess('Trial created successfully.');
      await loadTrials(session.token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to create trial.');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    api.clearSession();
    setSession(null);
    setTrials([]);
    setSuccess('Signed out.');
  };

  if (!session) {
    return (
      <div className="card" style={{ maxWidth: 560 }}>
        <div className="card-header">
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Phase 2
            </div>
            <h2 className="card-title">Trial Access</h2>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <button
            type="button"
            className={`btn ${authMode === 'register' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setAuthMode('register')}
          >
            Register
          </button>
          <button
            type="button"
            className={`btn ${authMode === 'login' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setAuthMode('login')}
          >
            Login
          </button>
        </div>

        <form onSubmit={handleAuthSubmit}>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Email</div>
              <input
                value={authForm.email}
                onChange={(event) => setAuthForm((current) => ({ ...current, email: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                type="email"
                required
              />
            </label>

            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Password</div>
              <input
                value={authForm.password}
                onChange={(event) => setAuthForm((current) => ({ ...current, password: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                type="password"
                required
              />
            </label>

            {error ? (
              <div style={{ color: '#fca5a5', background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                {error}
              </div>
            ) : null}

            {success ? (
              <div style={{ color: '#86efac', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '0.75rem', borderRadius: '0.5rem' }}>
                {success}
              </div>
            ) : null}

            <button type="submit" className="btn btn-primary" disabled={authLoading}>
              {authLoading ? <Loader2 size={16} className="spin" /> : <PlusCircle size={16} />}
              {authLoading ? 'Working...' : authMode === 'register' ? 'Create account' : 'Sign in'}
            </button>
          </div>
        </form>
      </div>
    );
  }

  const tokenLabel = session.user.email;

  return (
    <div style={{ display: 'grid', gap: '1.5rem' }}>
      <div className="card">
        <div className="card-header">
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Phase 2
            </div>
            <h2 className="card-title">Trial Portfolio</h2>
            <div className="card-subtitle">Signed in as {tokenLabel}</div>
          </div>

          <button type="button" className="btn btn-outline" onClick={handleLogout}>
            <LogOut size={16} />
            Sign out
          </button>
        </div>

        <form onSubmit={handleCreateTrial}>
          <div className="grid-2" style={{ alignItems: 'end' }}>
            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Trial code</div>
              <input
                value={trialForm.trial_code}
                onChange={(event) => setTrialForm((current) => ({ ...current, trial_code: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                required
              />
            </label>

            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Status</div>
              <select
                value={trialForm.status}
                onChange={(event) => setTrialForm((current) => ({ ...current, status: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              >
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </label>

            <label style={{ gridColumn: '1 / -1' }}>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Trial name</div>
              <input
                value={trialForm.trial_name}
                onChange={(event) => setTrialForm((current) => ({ ...current, trial_name: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                required
              />
            </label>

            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Start date</div>
              <input
                type="date"
                value={trialForm.start_date}
                onChange={(event) => setTrialForm((current) => ({ ...current, start_date: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </label>

            <label>
              <div style={{ marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>End date</div>
              <input
                type="date"
                value={trialForm.end_date}
                onChange={(event) => setTrialForm((current) => ({ ...current, end_date: event.target.value }))}
                style={{ width: '100%', padding: '0.7rem 0.8rem', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
              />
            </label>
          </div>

          {error ? (
            <div style={{ marginTop: '1rem', color: '#fca5a5', background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '0.75rem', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          ) : null}

          {success ? (
            <div style={{ marginTop: '1rem', color: '#86efac', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '0.75rem', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={16} />
              <span>{success}</span>
            </div>
          ) : null}

          <div style={{ marginTop: '1rem' }}>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? <Loader2 size={16} className="spin" /> : <ClipboardList size={16} />}
              {creating ? 'Creating trial...' : 'Create trial'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">My trials</h3>
            <div className="card-subtitle">{trials.length} total records</div>
          </div>
        </div>

        {loadingTrials ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
            <Loader2 size={16} className="spin" />
            Loading trials…
          </div>
        ) : trials.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', padding: '1rem 0' }}>
            No trials yet. Create your first study to start tracking enrollment and operational status.
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Participants</th>
                  <th>Dates</th>
                </tr>
              </thead>
              <tbody>
                {trials.map((trial) => (
                  <tr key={trial.id}>
                    <td>{trial.trial_code}</td>
                    <td>{trial.trial_name}</td>
                    <td>{trial.status}</td>
                    <td>{trial.participant_count}</td>
                    <td>
                      {trial.start_date || '—'}
                      {trial.end_date ? ` → ${trial.end_date}` : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
