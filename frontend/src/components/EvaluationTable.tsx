import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { EvaluationCreate, Skill } from '../types/api';

interface EvaluationTableProps {
  skillId?: number;
  skill?: Skill;
}

export function EvaluationTable({ skillId, skill }: EvaluationTableProps) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [showCreate, setShowCreate] = useState(false);
  const [newEvaluation, setNewEvaluation] = useState<EvaluationCreate>({
    skill_id: skillId || 0,
    model_name: '',
    model_version: '',
    provider: 'openai-compatible',
    sample_size: 5,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['evaluations', skillId, page, pageSize, status],
    queryFn: () => skillId ? api.getEvaluations(skillId, { page, page_size: pageSize, status }) : Promise.resolve({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }),
    enabled: !!skillId,
  });

  const createMutation = useMutation({
    mutationFn: (data: EvaluationCreate) => api.createEvaluation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations', skillId] });
      setShowCreate(false);
      setNewEvaluation({ ...newEvaluation, model_name: '', model_version: '' });
    },
  });

  if (isLoading && !data) {
    return <div className="loading"><div className="spinner" /></div>;
  }

  if (error) {
    return (
      <div className="alert alert-error">
        Failed to load evaluations: {(error as Error).message}
      </div>
    );
  }

  const evaluations = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEvaluation.model_name || !newEvaluation.model_version) return;
    createMutation.mutate(newEvaluation);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <span className="badge badge-success">Completed</span>;
      case 'running': return <span className="badge badge-info">Running</span>;
      case 'failed': return <span className="badge badge-error">Failed</span>;
      default: return <span className="badge badge-warning">Pending</span>;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <h2>Evaluations {skill && <span style={{ fontWeight: 'normal', color: 'var(--color-text-muted)', fontSize: '1rem' }}>for {skill.display_name}</span>}</h2>
        <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary">
          {showCreate ? 'Cancel' : 'New Evaluation'}
        </button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <form onSubmit={handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
              <div className="form-group">
                <label className="form-label">Model Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={newEvaluation.model_name}
                  onChange={(e) => setNewEvaluation({ ...newEvaluation, model_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Model Version</label>
                <input
                  type="text"
                  className="form-input"
                  value={newEvaluation.model_version}
                  onChange={(e) => setNewEvaluation({ ...newEvaluation, model_version: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Provider</label>
                <select className="form-input" value={newEvaluation.provider} onChange={(e) => setNewEvaluation({ ...newEvaluation, provider: e.target.value })}>
                  <option value="openai-compatible">OpenAI Compatible</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Gemini</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Sample Size</label>
                <input
                  type="number"
                  className="form-input"
                  min="1"
                  max="100"
                  value={newEvaluation.sample_size}
                  onChange={(e) => setNewEvaluation({ ...newEvaluation, sample_size: Number(e.target.value) })}
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-md)' }}>
              <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Evaluation'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginBottom: 'var(--spacing-md)' }}>
        <label className="form-label" style={{ display: 'inline-block', marginRight: 'var(--spacing-sm)' }}>Filter by Status:</label>
        <select className="form-input" style={{ width: 'auto', display: 'inline-block' }} value={status || ''} onChange={(e) => { setStatus(e.target.value || undefined); setPage(1); }}>
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Version</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Score</th>
              <th>Confidence</th>
              <th>Passed</th>
              <th>Sample Size</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {evaluations.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                  <div className="empty-state">
                    <h3>No evaluations found</h3>
                    <p>Create your first evaluation to get started.</p>
                  </div>
                </td>
              </tr>
            ) : (
              evaluations.map((evaluation) => (
                <tr key={evaluation.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{evaluation.model_name}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{evaluation.model_version}</td>
                  <td><span className="badge badge-info">{evaluation.provider}</span></td>
                  <td>{getStatusBadge(evaluation.status)}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {evaluation.score !== null ? evaluation.score.toFixed(3) : '—'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {evaluation.confidence_lower !== null && evaluation.confidence_upper !== null
                      ? `[${evaluation.confidence_lower.toFixed(3)}, ${evaluation.confidence_upper.toFixed(3)}]`
                      : '—'}
                  </td>
                  <td>
                    {evaluation.passed === true ? <span className="badge badge-success">Yes</span> : 
                     evaluation.passed === false ? <span className="badge badge-error">No</span> : '—'}
                  </td>
                  <td>{evaluation.sample_size}</td>
                  <td style={{ fontSize: '0.875rem' }}>{new Date(evaluation.created_at).toLocaleDateString()}</td>
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