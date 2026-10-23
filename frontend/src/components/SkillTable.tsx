import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Skill } from '../types/api';

interface SkillTableProps {
  onEdit?: (skill: Skill) => void;
  onDelete?: (skill: Skill) => void;
}

export function SkillTable({ onEdit, onDelete }: SkillTableProps) {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [isActive, setIsActive] = useState<boolean | undefined>(undefined);

  const { data, isLoading, error } = useQuery({
    queryKey: ['skills', page, pageSize, search, category, isActive],
    queryFn: () => api.getSkills({ page, page_size: pageSize, search: search || undefined, category, is_active: isActive }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteSkill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  const handleDelete = (skill: Skill) => {
    if (window.confirm(`Delete skill "${skill.display_name}"?`)) {
      if (onDelete) {
        onDelete(skill);
      } else {
        deleteMutation.mutate(skill.id);
      }
    }
  };

  const handleEdit = (skill: Skill) => {
    if (onEdit) {
      onEdit(skill);
    }
  };

  if (isLoading && !data) {
    return <div className="loading"><div className="spinner" /></div>;
  }

  if (error) {
    return (
      <div className="alert alert-error">
        Failed to load skills: {(error as Error).message}
      </div>
    );
  }

  const skills = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.total_pages || 1;

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-lg)', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="form-label">Search</label>
          <input
            type="text"
            className="form-input"
            placeholder="Search skills..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <div style={{ minWidth: 150 }}>
          <label className="form-label">Category</label>
          <select className="form-input" value={category || ''} onChange={(e) => { setCategory(e.target.value || undefined); setPage(1); }}>
            <option value="">All Categories</option>
            <option value="evaluation">Evaluation</option>
            <option value="drift">Drift Detection</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
            <option value="quality">Code Quality</option>
          </select>
        </div>
        <div style={{ minWidth: 120 }}>
          <label className="form-label">Status</label>
          <select className="form-input" value={isActive !== undefined ? String(isActive) : ''} onChange={(e) => { setIsActive(e.target.value === '' ? undefined : e.target.value === 'true'); setPage(1); }}>
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <div style={{ minWidth: 100 }}>
          <label className="form-label">Page Size</label>
          <select className="form-input" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Display Name</th>
              <th>Category</th>
              <th>Version</th>
              <th>Status</th>
              <th>Created</th>
              <th style={{ width: '120px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {skills.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                  <div className="empty-state">
                    <h3>No skills found</h3>
                    <p>Create your first skill to get started.</p>
                  </div>
                </td>
              </tr>
            ) : (
              skills.map((skill) => (
                <tr key={skill.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{skill.name}</td>
                  <td>{skill.display_name}</td>
                  <td><span className="badge badge-info">{skill.category}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{skill.version}</td>
                  <td>
                    <span className={skill.is_active ? 'badge badge-success' : 'badge badge-error'}>
                      {skill.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.875rem' }}>{new Date(skill.created_at).toLocaleDateString()}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
                      <button
                        onClick={() => handleEdit(skill)}
                        className="btn btn-ghost"
                        style={{ padding: 'var(--spacing-xs)', fontSize: '0.875rem' }}
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(skill)}
                        className="btn btn-ghost"
                        style={{ padding: 'var(--spacing-xs)', fontSize: '0.875rem', color: 'var(--color-error)' }}
                        title="Delete"
                        disabled={deleteMutation.isPending}
                      >
                        🗑️
                      </button>
                    </div>
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