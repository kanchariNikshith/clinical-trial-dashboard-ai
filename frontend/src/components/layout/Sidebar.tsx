import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  FolderKanban,
  FileSpreadsheet,
  BarChart3,
  Sparkles,
  FileText,
  ShieldCheck,
  Info,
  Server,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'status', label: 'System Health', path: '/', icon: Server, phase: 'Phase 0' },
  { id: 'trials', label: 'Trials Overview', path: '/trials', icon: FolderKanban, phase: 'Phase 2' },
  { id: 'import', label: 'CSV Import & Preview', path: '/import', icon: FileSpreadsheet, phase: 'Phase 3' },
  { id: 'dashboard', label: 'Trial Metrics', path: '/dashboard', icon: BarChart3, phase: 'Phase 4' },
  { id: 'ai-insights', label: 'AI Advisory Insights', path: '/ai-insights', icon: Sparkles, phase: 'Phase 5' },
  { id: 'reports', label: 'Reports & Export', path: '/reports', icon: FileText, phase: 'Phase 6' },
  { id: 'audit', label: 'Audit Log', path: '/audit', icon: ShieldCheck, phase: 'Phase 6' },
  { id: 'about', label: 'About & Governance', path: '/about', icon: Info, phase: 'Doc' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon">
          <Activity size={18} />
        </div>
        <div>
          <div className="brand-title">TrialMetrics</div>
          <div className="brand-subtitle">Clinical Analytics MVP</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.id}
              to={item.path}
              id={`nav-${item.id}`}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              <span className="nav-phase-badge">{item.phase}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div><strong>MVP Prototype</strong></div>
        <div style={{ marginTop: '0.2rem', color: '#64748b' }}>Synthetic / De-identified data only</div>
      </div>
    </aside>
  );
};
