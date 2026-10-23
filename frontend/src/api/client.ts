import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { PaginatedResponse, Skill, SkillCreate, SkillUpdate, Evaluation, EvaluationCreate, DriftReport, AuditLog, HealthResponse, User } from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => config,
      (error: AxiosError) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async getSkills(params?: { page?: number; page_size?: number; category?: string; is_active?: boolean; search?: string }): Promise<PaginatedResponse<Skill>> {
    const response = await this.client.get<PaginatedResponse<Skill>>('/skills', { params });
    return response.data;
  }

  async getSkill(id: number): Promise<Skill> {
    const response = await this.client.get<Skill>(`/skills/${id}`);
    return response.data;
  }

  async getSkillByName(name: string): Promise<Skill> {
    const response = await this.client.get<Skill>(`/skills/by-name/${encodeURIComponent(name)}`);
    return response.data;
  }

  async createSkill(data: SkillCreate): Promise<Skill> {
    const response = await this.client.post<Skill>('/skills', data);
    return response.data;
  }

  async updateSkill(id: number, data: SkillUpdate): Promise<Skill> {
    const response = await this.client.patch<Skill>(`/skills/${id}`, data);
    return response.data;
  }

  async deleteSkill(id: number): Promise<void> {
    await this.client.delete(`/skills/${id}`);
  }

  async createEvaluation(data: EvaluationCreate): Promise<Evaluation> {
    const response = await this.client.post<Evaluation>(`/skills/${data.skill_id}/evaluate`, data);
    return response.data;
  }

  async getEvaluations(skillId: number, params?: { page?: number; page_size?: number; status?: string }): Promise<PaginatedResponse<Evaluation>> {
    const response = await this.client.get<PaginatedResponse<Evaluation>>(`/skills/${skillId}/evaluations`, { params });
    return response.data;
  }

  async getEvaluation(id: number): Promise<Evaluation> {
    const response = await this.client.get<Evaluation>(`/skills/evaluations/${id}`);
    return response.data;
  }

  async getDriftReports(params?: { page?: number; page_size?: number; skill_id?: number }): Promise<PaginatedResponse<DriftReport>> {
    const response = await this.client.get<PaginatedResponse<DriftReport>>('/drift/reports', { params });
    return response.data;
  }

  async createDriftReport(data: {
    skill_id: number;
    baseline_model: string;
    baseline_version: string;
    compare_model: string;
    compare_version: string;
    regression_detected: boolean;
    effect_size?: number;
    p_value?: number;
    confidence_level?: number;
    details?: Record<string, unknown>;
  }): Promise<DriftReport> {
    const response = await this.client.post<DriftReport>('/drift/reports', data);
    return response.data;
  }

  async getAuditLogs(params?: { page?: number; page_size?: number; user_id?: string; action?: string }): Promise<PaginatedResponse<AuditLog>> {
    const response = await this.client.get<PaginatedResponse<AuditLog>>('/drift/audit-logs', { params });
    return response.data;
  }

  async login(): Promise<void> {
    await this.client.get('/auth/login');
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  async demoLogin(): Promise<User> {
    const response = await this.client.get<User>('/auth/demo-login');
    return response.data;
  }
}

export const api = new ApiClient();