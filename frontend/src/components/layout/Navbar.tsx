import React from 'react';
import type { HealthResponse } from '../../types';
import { Shield, ExternalLink } from 'lucide-react';


interface NavbarProps {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({ health, loading, error }) => {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <h1 className="page-title" id="main-heading">
          Operational Dashboard
        </h1>
      </div>

      <div className="navbar-right">
        {/* Backend health pill */}
        <div
          className="status-indicator"
          id="backend-health-indicator"
          title={
            error
              ? `Backend Connection Error: ${error}`
              : health
              ? `Connected to Backend v${health.version} (${health.environment})`
              : 'Checking API...'
          }
        >
          <span
            className={`status-dot ${
              loading ? 'checking' : error ? 'error' : 'healthy'
            }`}
          />
          <span>
            {loading
              ? 'Checking API...'
              : error
              ? 'Backend Offline'
              : `API ${health?.status || 'Online'}`}
          </span>
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="btn btn-outline"
          style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
          id="docs-link"
        >
          <span>OpenAPI Docs</span>
          <ExternalLink size={13} />
        </a>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            paddingLeft: '0.75rem',
            borderLeft: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              backgroundColor: 'var(--bg-surface-elevated)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
            }}
          >
            <Shield size={16} />
          </div>
          <div style={{ fontSize: '0.8rem' }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Demo Session</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Phase 0 Unauthenticated</div>
          </div>
        </div>
      </div>
    </header>
  );
};
