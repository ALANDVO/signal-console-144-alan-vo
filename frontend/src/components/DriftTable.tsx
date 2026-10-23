import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export function DriftTable() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [skillId, setSkillId] = useState<number | undefined>(undefined);

  const { data, isLoading, error } = useQuery({
    queryKey: ['drift-reports', page, pageSize, skillId],
    queryFn: () => api.getDriftReports({ page, page_size: pageSize, skill_id: skillId }),
  });

  if (isLoading && !data) {
    return <div className="loading"><div className="spinner" /></div>;
  }

  if (error) {
    return (
      <div className="alert alert-error">
        Failed to load drift reports: {(error as Error).message}
      </div>
    );
  }

  const reports = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  const getRegressionBadge = (detected: boolean) => (
    <span className={detected ? 'badge badge-error' : 'badge badge-success'}>
      {detected ? 'Regression Detected' : 'No Regression'}
    </span>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <h2>Drift Reports</h2>
      </div>

      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        <label className="form-label" style={{ display: 'inline-block', marginRight: 'var(--spacing-sm)' }}>Skill ID:</label>
        <input
          type="number"
          className="form-input"
          style={{ width: 'auto', display: 'inline-block', maxWidth: '200px' }}
          placeholder="Filter by skill ID"
          value={skillId || ''}
          onChange={(e) => { setSkillId(e.target.value ? Number(e.target.value) : undefined); setPage(1); }}
        />
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Skill ID</th>
              <th>Baseline</th>
              <th>Compare</th>
              <th>Regression</th>
              <th>Effect Size</th>
              <th>P-Value</th>
              <th>Confidence</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {reports.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                  <div className="empty-state">
                    <h3>No drift reports found</h3>
                    <p>Run drift detection to compare model versions.</p>
                  </div>
                </td>
              </tr>
            ) : (
              reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.skill_id}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {report.baseline_model} {report.baseline_version}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {report.compare_model} {report.compare_version}
                  </td>
                  <td>{getRegressionBadge(report.regression_detected)}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {report.effect_size !== null ? report.effect_size.toFixed(4) : '—'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {report.p_value !== null ? report.p_value.toFixed(4) : '—'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {(report.confidence_level * 100).toFixed(0)}%
                  </td>
                  <td style={{ fontSize: '0.875rem' }}>{new Date(report.created_at).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1 || isLoading}>
            Previous
          </button>
          <span style={{ padding: '0 var(--spacing-md)' }}>
            Page {page} of {totalPages} ({total} total)
          </span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages || isLoading}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}