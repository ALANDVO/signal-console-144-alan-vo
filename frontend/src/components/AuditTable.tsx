import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export function AuditTable() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [userId, setUserId] = useState('');
  const [action, setAction] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['audit-logs', page, pageSize, userId, action],
    queryFn: () => api.getAuditLogs({ page, page_size: pageSize, user_id: userId || undefined, action: action || undefined }),
  });

  if (isLoading && !data) {
    return <div className="loading"><div className="spinner" /></div>;
  }

  if (error) {
    return (
      <div className="alert alert-error">
        Failed to load audit logs: {(error as Error).message}
      </div>
    );
  }

  const logs = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  return (
    <div>
      <h2 style={{ marginBottom: 'var(--spacing-lg)' }}>Audit Logs</h2>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="form-label">User ID</label>
          <input
            type="text"
            className="form-input"
            placeholder="Filter by user ID"
            value={userId}
            onChange={(e) => { setUserId(e.target.value); setPage(1); }}
          />
        </div>
        <div style={{ minWidth: 200 }}>
          <label className="form-label">Action</label>
          <input
            type="text"
            className="form-input"
            placeholder="Filter by action"
            value={action}
            onChange={(e) => { setAction(e.target.value); setPage(1); }}
          />
        </div>
        <div style={{ minWidth: 100 }}>
          <label className="form-label">Page Size</label>
          <select className="form-input" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Resource ID</th>
              <th>IP Address</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                  <div className="empty-state">
                    <h3>No audit logs found</h3>
                    <p>Audit logs will appear here as users interact with the system.</p>
                  </div>
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: '0.875rem', whiteSpace: 'nowrap' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {log.user_id || '—'}
                  </td>
                  <td><span className="badge badge-info">{log.action}</span></td>
                  <td>{log.resource_type}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {log.resource_id || '—'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {log.ip_address || '—'}
                  </td>
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