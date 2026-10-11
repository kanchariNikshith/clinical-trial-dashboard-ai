import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, FileSpreadsheet, ShieldAlert, UploadCloud } from 'lucide-react';
import { api, ApiClientError } from '../api/client';
import type { Trial } from '../types/trials';

interface PreviewRecord {
  participant_id: string;
  status: string;
  visits_completed?: number | null;
  visits_planned?: number | null;
  enrollment_date?: string | null;
  last_visit_date?: string | null;
  next_visit_due_date?: string | null;
}

export const ImportPage: React.FC = () => {
  const [trials, setTrials] = useState<Trial[]>([]);
  const [selectedTrialId, setSelectedTrialId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<PreviewRecord[]>([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [summary, setSummary] = useState({ total_rows: 0, valid_rows: 0, invalid_rows: 0 });
  const [isLoadingTrials, setIsLoadingTrials] = useState(true);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmImport, setConfirmImport] = useState(false);

  useEffect(() => {
    const loadTrials = async () => {
      setIsLoadingTrials(true);
      try {
        const response = await api.getTrials();
        setTrials(response.trials);
        if (response.trials.length > 0) {
          setSelectedTrialId(response.trials[0].id);
        }
      } catch (err) {
        const typed = err as ApiClientError;
        if (typed.code === 'HTTP_401' || typed.message.toLowerCase().includes('expired')) {
          localStorage.removeItem('access_token');
          setError('Your session expired. Please sign in again to upload a CSV.');
        } else {
          setError('Unable to load your trials. Please check your session and try again.');
        }
      } finally {
        setIsLoadingTrials(false);
      }
    };

    void loadTrials();
  }, []);

  const rowsToShow = useMemo(() => previewRows.slice(0, 25), [previewRows]);

  const handlePreview = async () => {
    if (!selectedTrialId || !selectedFile) {
      setError('Choose a trial and a CSV file before previewing.');
      return;
    }

    setError(null);
    setMessage(null);
    setIsPreviewing(true);

    try {
      const result = await api.previewParticipants(selectedTrialId, selectedFile);
      setPreviewRows(result.preview ?? []);
      setValidationErrors(result.errors ?? []);
      setSummary({
        total_rows: result.total_rows,
        valid_rows: result.valid_rows,
        invalid_rows: result.invalid_rows,
      });

      if (result.invalid_rows > 0) {
        setMessage('Preview ready with validation issues. Fix the rows before importing.');
      } else {
        setMessage('Preview successful. You can import this file after confirming.');
      }
    } catch (err) {
      const typed = err as ApiClientError;
      if (typed.code === 'HTTP_401' || typed.message.toLowerCase().includes('expired')) {
        localStorage.removeItem('access_token');
        setError('Your session expired. Please sign in again.');
        setValidationErrors([]);
        setSummary({ total_rows: 0, valid_rows: 0, invalid_rows: 0 });
        setPreviewRows([]);
        return;
      }
      setError(typed.message || 'The CSV could not be validated.');
      setValidationErrors(typed.details || []);
      setSummary({ total_rows: 0, valid_rows: 0, invalid_rows: 0 });
      setPreviewRows([]);
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleImport = async () => {
    if (!selectedTrialId || !selectedFile) {
      setError('Choose a trial and a CSV file before importing.');
      return;
    }

    if (!confirmImport) {
      setError('Confirm the import before writing participant records to the database.');
      return;
    }

    setError(null);
    setMessage(null);
    setIsImporting(true);

    try {
      const result = await api.importParticipants(selectedTrialId, selectedFile, true);
      setSummary({
        total_rows: result.total_rows,
        valid_rows: result.valid_rows,
        invalid_rows: result.invalid_rows,
      });
      setValidationErrors(result.errors ?? []);
      setPreviewRows(result.preview ?? []);
      setMessage(`Import succeeded: ${result.imported_count} participants were created.`);
      setConfirmImport(false);
    } catch (err) {
      const typed = err as ApiClientError;
      if (typed.code === 'HTTP_401' || typed.message.toLowerCase().includes('expired')) {
        localStorage.removeItem('access_token');
        setError('Your session expired. Please sign in again.');
        setValidationErrors([]);
        setSummary({ total_rows: 0, valid_rows: 0, invalid_rows: 0 });
        setPreviewRows([]);
        return;
      }
      setError(typed.message || 'The import failed and no partial records were saved.');
      setValidationErrors(typed.details || []);
      setSummary({ total_rows: 0, valid_rows: 0, invalid_rows: 0 });
      setPreviewRows([]);
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <section style={{ display: 'grid', gap: '1.25rem', padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <FileSpreadsheet size={28} color="#2563eb" />
        <div>
          <h1 style={{ margin: 0 }}>CSV Import & Preview</h1>
          <p style={{ margin: '0.25rem 0 0', color: '#475569' }}>
            Validate participant rows server-side before importing into a trial.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '1rem', background: '#fff', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 8px 18px rgba(15, 23, 42, 0.06)' }}>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          <label style={{ display: 'grid', gap: '0.4rem', fontWeight: 600 }}>
            Trial
            <select
              value={selectedTrialId}
              onChange={(event) => setSelectedTrialId(event.target.value)}
              style={{ padding: '0.7rem 0.8rem', borderRadius: '8px', border: '1px solid #cbd5e1' }}
              disabled={isLoadingTrials || trials.length === 0}
            >
              {trials.length === 0 ? <option value="">No trials available</option> : null}
              {trials.map((trial) => (
                <option key={trial.id} value={trial.id}>
                  {trial.trial_code} — {trial.trial_name}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: 'grid', gap: '0.4rem', fontWeight: 600 }}>
            CSV file
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              style={{ padding: '0.7rem', borderRadius: '8px', border: '1px solid #cbd5e1' }}
            />
          </label>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={handlePreview}
            disabled={!selectedFile || !selectedTrialId || isPreviewing || isImporting}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: 'none',
              background: '#2563eb',
              color: '#fff',
              fontWeight: 700,
              cursor: !selectedFile || !selectedTrialId ? 'not-allowed' : 'pointer',
              opacity: !selectedFile || !selectedTrialId ? 0.6 : 1,
            }}
          >
            {isPreviewing ? 'Validating…' : 'Preview CSV'}
          </button>

          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
            <input type="checkbox" checked={confirmImport} onChange={(event) => setConfirmImport(event.target.checked)} />
            Confirm import
          </label>

          <button
            type="button"
            onClick={handleImport}
            disabled={!selectedFile || !selectedTrialId || !confirmImport || isImporting || isPreviewing}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: 'none',
              background: '#0f766e',
              color: '#fff',
              fontWeight: 700,
              cursor: !selectedFile || !selectedTrialId || !confirmImport ? 'not-allowed' : 'pointer',
              opacity: !selectedFile || !selectedTrialId || !confirmImport ? 0.6 : 1,
            }}
          >
            {isImporting ? 'Importing…' : 'Import now'}
          </button>
        </div>

        {error ? (
          <div style={{ display: 'grid', gap: '0.65rem', color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px', padding: '0.8rem 1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldAlert size={18} />
              <span>{error}</span>
            </div>
            {validationErrors.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#991b1b', display: 'grid', gap: '0.25rem' }}>
                {validationErrors.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        {message ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#065f46', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '10px', padding: '0.8rem 1rem' }}>
            {summary.invalid_rows > 0 ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
            <span>{message}</span>
          </div>
        ) : null}
      </div>

      {summary.total_rows > 0 || validationErrors.length > 0 ? (
        <div style={{ display: 'grid', gap: '1rem', background: '#fff', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 8px 18px rgba(15, 23, 42, 0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <UploadCloud size={18} color="#0f172a" />
            <strong>Summary</strong>
          </div>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <span style={{ background: '#e2e8f0', borderRadius: '999px', padding: '0.35rem 0.75rem' }}>Total rows: {summary.total_rows}</span>
            <span style={{ background: '#dcfce7', borderRadius: '999px', padding: '0.35rem 0.75rem' }}>Valid rows: {summary.valid_rows}</span>
            <span style={{ background: '#fee2e2', borderRadius: '999px', padding: '0.35rem 0.75rem' }}>Invalid rows: {summary.invalid_rows}</span>
          </div>

          {validationErrors.length > 0 ? (
            <div>
              <h3 style={{ marginBottom: '0.5rem' }}>Validation issues</h3>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#b91c1c', display: 'grid', gap: '0.35rem' }}>
                {validationErrors.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {rowsToShow.length > 0 ? (
        <div style={{ background: '#fff', borderRadius: '12px', padding: '1.25rem', boxShadow: '0 8px 18px rgba(15, 23, 42, 0.06)', overflowX: 'auto' }}>
          <h3 style={{ marginTop: 0 }}>Preview</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Participant</th>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Visits</th>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Enrollment</th>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Last visit</th>
                <th style={{ textAlign: 'left', padding: '0.6rem', borderBottom: '1px solid #e2e8f0' }}>Next due</th>
              </tr>
            </thead>
            <tbody>
              {rowsToShow.map((row, index) => (
                <tr key={`${row.participant_id}-${index}`}>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>{row.participant_id}</td>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>{row.status}</td>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>
                    {row.visits_completed ?? '-'} / {row.visits_planned ?? '-'}
                  </td>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>{row.enrollment_date ?? '-'}</td>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>{row.last_visit_date ?? '-'}</td>
                  <td style={{ padding: '0.6rem', borderBottom: '1px solid #f1f5f9' }}>{row.next_visit_due_date ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!trials.length && !isLoadingTrials ? (
        <div style={{ padding: '1rem', borderRadius: '10px', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
          Create a trial before uploading participant CSV files.
        </div>
      ) : null}
    </section>
  );
};

export default ImportPage;
