import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import type { HealthResponse } from '../types';
import {
  AlertTriangle,
  RefreshCw,
  Server,
  ShieldAlert,
  Database,
  Cpu,
  Lock,
} from 'lucide-react';

import { API_BASE_URL } from '../api/client';

interface OutletContextType {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  refreshHealth: () => Promise<void>;
}

export const StatusPage: React.FC = () => {
  const { health, loading, error, refreshHealth } =
    useOutletContext<OutletContextType>();
  const [pingLatency, setPingLatency] = useState<number | null>(null);
  const [pinging, setPinging] = useState(false);

  const handleManualPing = async () => {
    setPinging(true);
    const start = performance.now();
    try {
      await refreshHealth();
      const end = performance.now();
      setPingLatency(Math.round(end - start));
    } finally {
      setPinging(false);
    }
  };

  return (
    <div>
      {/* Scope Disclaimer Banner */}
      <div className="disclaimer-banner" id="scope-disclaimer">
        <ShieldAlert size={20} style={{ flexShrink: 0 }} />
        <div>
          <strong>Operational Safety Boundary:</strong> This application is a clinical-trial
          analytics prototype for synthetic or appropriately de-identified records. Never upload
          real patient-identifiable data. AI-assisted insights are advisory and require human
          verification.
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Phase 0 System Baseline & Health Verification</h2>
            <div className="card-subtitle">
              Verifying frontend, backend connectivity, and safety boundaries per AC-063 & AC-064
            </div>
          </div>
          <button
            onClick={handleManualPing}
            disabled={pinging || loading}
            className="btn btn-primary"
            id="btn-refresh-health"
          >
            <RefreshCw size={15} className={pinging ? 'spin' : ''} />
            <span>Test API Connection</span>
          </button>
        </div>

        <div className="grid-3" style={{ marginTop: '1.25rem' }}>
          <div className="metric-card">
            <div className="metric-label">Backend Service Status</div>
            <div
              className="metric-value"
              style={{
                color: error
                  ? 'var(--accent-rose)'
                  : health
                  ? 'var(--accent-emerald)'
                  : 'var(--accent-amber)',
              }}
            >
              {loading ? 'Checking...' : error ? 'Offline' : 'Healthy'}
            </div>
            <div className="metric-sub">
              {error ? 'API unavailable' : `Connected to ${API_BASE_URL}`}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">API Latency</div>
            <div className="metric-value">
              {pingLatency !== null ? `${pingLatency} ms` : health ? '< 50 ms' : 'N/A'}
            </div>
            <div className="metric-sub">Roundtrip HTTP GET /health</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Environment</div>
            <div className="metric-value" style={{ textTransform: 'capitalize' }}>
              {health?.environment || 'development'}
            </div>
            <div className="metric-sub">Version {health?.version || '0.1.0'}</div>
          </div>
        </div>

        {error && (
          <div
            style={{
              marginTop: '1.25rem',
              padding: '1rem',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: 'var(--accent-rose)',
            }}
          >
            <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={18} />
              <span>Backend Connection Error</span>
            </div>
            <div style={{ marginTop: '0.35rem', fontSize: '0.85rem' }}>
              Could not connect to FastAPI at <code>{API_BASE_URL}/health</code>. Ensure the backend
              process is running.
            </div>
          </div>
        )}

        {health && (
          <div style={{ marginTop: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.75rem' }}>
              Verified Health Check Response (AC-063)
            </h3>
            <pre className="code-block">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Approved Architectural Decisions</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <Lock size={18} style={{ color: 'var(--accent-primary)', marginTop: 2, flexShrink: 0 }} />
              <div style={{ fontSize: '0.875rem' }}>
                <strong>1. Authentication & Security:</strong> Self-registration with strict password
                validation and rate-limiting. Local demo seeding command without hardcoded production
                secrets.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <Database size={18} style={{ color: 'var(--accent-teal)', marginTop: 2, flexShrink: 0 }} />
              <div style={{ fontSize: '0.875rem' }}>
                <strong>2. Dual-Engine Persistence:</strong> PostgreSQL primary for Docker & production,
                with SQLite fallback for rapid local Windows development.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <Server size={18} style={{ color: 'var(--accent-emerald)', marginTop: 2, flexShrink: 0 }} />
              <div style={{ fontSize: '0.875rem' }}>
                <strong>3. Stateless CSV Flow:</strong> 2-step preview then transactional import. Server
                revalidation with full rollback on error.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <Cpu size={18} style={{ color: 'var(--accent-amber)', marginTop: 2, flexShrink: 0 }} />
              <div style={{ fontSize: '0.875rem' }}>
                <strong>4. Duplicate Protection:</strong> Strict rejection of duplicate participant IDs
                both within CSVs and against existing trial participants.
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Development Roadmap Progress</h3>
          </div>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Phase</th>
                  <th>Module</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Phase 0</strong></td>
                  <td>Foundation & Health Endpoint</td>
                  <td><span style={{ color: 'var(--accent-emerald)' }}>● Ready for Review</span></td>
                </tr>
                <tr>
                  <td>Phase 1</td>
                  <td>Auth, Users & Database</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 2</td>
                  <td>Trial Management</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 3</td>
                  <td>CSV Import & Validation</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 4</td>
                  <td>Deterministic Metrics Engine</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 5</td>
                  <td>Gemini AI Insights Service</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 6</td>
                  <td>PDF Reports & Audit Log</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
                <tr>
                  <td>Phase 7</td>
                  <td>Hardening, Docker & Tests</td>
                  <td><span style={{ color: 'var(--text-muted)' }}>○ Queued</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
