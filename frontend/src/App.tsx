import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/layout/Shell';
import { StatusPage } from './pages/StatusPage';
import { TrialsPage } from './pages/TrialsPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { ImportPage } from './pages/ImportPage';
import { MetricsPage } from './pages/MetricsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell />}>
          <Route index element={<StatusPage />} />

          <Route path="trials" element={<TrialsPage />} />

          <Route path="import" element={<ImportPage />} />

          <Route path="dashboard" element={<MetricsPage />} />

          <Route
            path="ai-insights"
            element={
              <PlaceholderPage
                title="Google Gemini AI Advisory Insights"
                description="Aggregate-only AI narrative analysis with strict safety boundaries and provider timeout safeguards."
                phase="Phase 5"
                acceptanceCriteria={[
                  'AC-040: AI prompt sends only aggregated metrics; zero participant rows or identifiers.',
                  'AC-041: Dashboard and metrics remain functional if Gemini API key is missing or fails.',
                  'AC-042: AI narrative is labeled as advisory and requiring human verification.',
                  'AC-043: Model never invents completion dates or claims clinical efficacy/safety.',
                  'AC-044: Provider timeouts/errors do not expose credentials or stack traces.',
                ]}
              />
            }
          />

          <Route
            path="reports"
            element={
              <PlaceholderPage
                title="Clinical PDF Report Export"
                description="Server-generated ReportLab PDF summaries with verifiable backend metrics and safety disclaimers."
                phase="Phase 6"
                acceptanceCriteria={[
                  'AC-050: Authorized users can download valid PDF reports.',
                  'AC-051: PDF metrics match dashboard metrics endpoint exactly.',
                  'AC-052: Report includes trial identifier, generation timestamp, definitions, and caveats.',
                  'AC-053: AI section is explicitly labeled as AI-generated advisory content.',
                ]}
              />
            }
          />

          <Route
            path="audit"
            element={
              <PlaceholderPage
                title="Security & Operations Audit Log"
                description="Comprehensive audit trails for authentication, imports, AI queries, and PDF exports."
                phase="Phase 6"
                acceptanceCriteria={[
                  'AC-060: Actions (login, trial create, import, AI, PDF) logged per policy.',
                  'AC-061: Audit logs never store passwords, tokens, API keys, or raw CSV rows.',
                  'AC-062: Audit event access is restricted and user-scoped.',
                ]}
              />
            }
          />

          <Route
            path="about"
            element={
              <PlaceholderPage
                title="About TrialMetrics & Data Governance"
                description="Operational analytics prototype documentation, CSV schemas, and safety guidelines."
                phase="Reference"
                acceptanceCriteria={[
                  'Synthetic and de-identified study data only.',
                  'Advisory operational tool; not a medical device or EDC system.',
                  'Strict data minimization: no direct identifiers (names, emails, SSN, DOB).',
                ]}
              />
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
