/**
 * Type definitions for GrandmaScraper UI
 */

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  role: 'admin' | 'user' | 'readonly';
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface FieldConfig {
  name: string;
  selector: string;
  selector_type?: 'css' | 'xpath';
  type?: 'text' | 'number' | 'url';
  attribute?: 'text' | 'html' | 'href' | 'src' | 'value' | 'custom';
  selector_attribute?: string;
  custom_attribute?: string;
  multiple?: boolean;
  required?: boolean;
  default_value?: string;
}

export interface PaginationStrategy {
  type: 'none' | 'next_button' | 'url_pattern' | 'infinite_scroll';
  next_button_selector?: string;
  url_pattern?: string;
  max_scrolls?: number;
  scroll_wait_ms?: number;
}

export interface ScrapeJobConfig {
  name?: string;
  start_url: string;
  item_selector: string;
  item_selector_type?: 'css' | 'xpath';
  fields: FieldConfig[];
  pagination?: PaginationStrategy;
  max_pages?: number;
  max_items?: number;
  timeout_seconds?: number;
  retry_count?: number;
  fetcher_type?: 'auto' | 'requests' | 'browser';
  min_delay_ms?: number;
  max_delay_ms?: number;
  rate_limit?: number;
  concurrent_requests?: number;
  respect_robots_txt?: boolean;
}

export interface ScrapeJob {
  id: string;
  name: string;
  description?: string;
  config: ScrapeJobConfig;
  enabled: boolean;
  owner_id: string;
  schedule?: any;
  created_at: string;
  updated_at: string;
}

export interface ScrapeResult {
  id: string;
  job_id: string;
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  items: any[];
  total_items: number;
  pages_scraped: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  error_details?: any;
  warnings: string[];
  created_at: string;
}

export interface JobCreateData {
  name: string;
  description?: string;
  enabled: boolean;
  config: ScrapeJobConfig;
}

export interface JobUpdateData {
  name?: string;
  description?: string;
  enabled?: boolean;
  config?: ScrapeJobConfig;
}

export interface ApiError {
  detail: string;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface JobRunResponse {
  message: string;
  job_id: string;
  result_id: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
}

// Type aliases for convenience
export type UserCreate = RegisterData;
export type ScrapeJobCreate = JobCreateData;
