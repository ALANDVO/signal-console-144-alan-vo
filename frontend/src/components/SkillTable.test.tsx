import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { SkillTable } from './SkillTable';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getSkills: vi.fn(),
    createSkill: vi.fn(),
    updateSkill: vi.fn(),
    deleteSkill: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </QueryClientProvider>
);

describe('SkillTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', async () => {
    api.getSkills.mockResolvedValueOnce(new Promise(() => {}));
    
    render(<SkillTable />, { wrapper });
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders skills list', async () => {
    const mockSkills = {
      items: [
        { id: 1, name: 'test-skill', display_name: 'Test Skill', description: 'A test skill', category: 'evaluation', version: '1.0.0', schema: '{}', is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    
    api.getSkills.mockResolvedValueOnce(mockSkills);
    
    render(<SkillTable />, { wrapper });
    
    await screen.findByText('Test Skill');
    expect(screen.getByText('test-skill')).toBeInTheDocument();
    expect(screen.getByText('evaluation')).toBeInTheDocument();
  });

  it('renders empty state when no skills', async () => {
    const mockSkills = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    
    api.getSkills.mockResolvedValueOnce(mockSkills);
    
    render(<SkillTable />, { wrapper });
    
    await screen.findByText('No skills found');
    expect(screen.getByText('Create your first skill to get started.')).toBeInTheDocument();
  });
});