export interface Skill {
  id: number;
  name: string;
  display_name: string;
  description: string;
  category: string;
  version: string;
  schema: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SkillCreate {
  name: string;
  display_name: string;
  description: string;
  category: string;
  version?: string;
  schema: string;
  is_active?: boolean;
}

export interface SkillUpdate {
  display_name?: string;
  description?: string;
  category?: string;
  version?: string;
  schema?: string;
  is_active?: boolean;
}

export interface Evaluation {
  id: number;
  skill_id: number;
  model_name: string;
  model_version: string;
  provider: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  score: number | null;
  confidence_lower: number | null;
  confidence_upper: number | null;
  sample_size: number;
  passed: boolean | null;
  error_message: string | null;
  metadata: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface EvaluationCreate {
  skill_id: number;
  model_name: string;
  model_version: string;
  provider: string;
  sample_size?: number;
}

export interface DriftReport {
  id: number;
  skill_id: number;
  baseline_model: string;
  baseline_version: string;
  compare_model: string;
  compare_version: string;
  regression_detected: boolean;
  effect_size: number | null;
  p_value: number | null;
  confidence_level: number;
  details: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface User {
  user_id: string;
  roles: string[];
  email?: string;
  name?: string;
}