import React from 'react';
import { Clock, ShieldCheck, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  description: string;
  phase: string;
  acceptanceCriteria: string[];
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  description,
  phase,
  acceptanceCriteria,
}) => {
  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div
              style={{
                fontSize: '0.75rem',
                color: 'var(--accent-primary)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '0.25rem',
              }}
            >
              Scheduled for {phase}
            </div>
            <h2 className="card-title">{title}</h2>
            <div className="card-subtitle">{description}</div>
          </div>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              padding: '0.4rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
            }}
          >
            <Clock size={14} />
            <span>Implementation Queued</span>
          </span>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <h3
            style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.75rem',
            }}
          >
            Phase Acceptance Criteria Target
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {acceptanceCriteria.map((ac, idx) => (
              <li
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  fontSize: '0.875rem',
                  color: 'var(--text-primary)',
                }}
              >
                <ShieldCheck size={16} style={{ color: 'var(--accent-teal)', flexShrink: 0 }} />
                <span>{ac}</span>
              </li>
            ))}
          </ul>
        </div>

        <div
          style={{
            marginTop: '2rem',
            paddingTop: '1.25rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Proceeding to this module requires user approval of preceding phases.
          </span>
          <Link to="/" className="btn btn-outline" style={{ fontSize: '0.85rem' }}>
            <span>Back to System Status</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </div>
  );
};
