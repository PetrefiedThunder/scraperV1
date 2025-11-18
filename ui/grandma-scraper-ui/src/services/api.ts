/**
 * API service for GrandmaScraper backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginCredentials,
  RegisterData,
  AuthToken,
  ScrapeJob,
  ScrapeResult,
  JobCreateData,
  JobUpdateData,
  PaginationParams,
  JobRunResponse,
  HealthResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 responses
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.client.post<AuthToken>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  }

  async register(data: RegisterData): Promise<User> {
    const response = await this.client.post<User>('/auth/register', data);
    return response.data;
  }

  // Users
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/users/me');
    return response.data;
  }

  async updateCurrentUser(data: Partial<User>): Promise<User> {
    const response = await this.client.put<User>('/users/me', data);
    return response.data;
  }

  // Jobs
  async getJobs(params?: PaginationParams): Promise<ScrapeJob[]> {
    const response = await this.client.get<ScrapeJob[]>('/jobs/', { params });
    return response.data;
  }

  async getJob(id: string): Promise<ScrapeJob> {
    const response = await this.client.get<ScrapeJob>(`/jobs/${id}`);
    return response.data;
  }

  async createJob(data: JobCreateData): Promise<ScrapeJob> {
    const response = await this.client.post<ScrapeJob>('/jobs/', data);
    return response.data;
  }

  async updateJob(id: string, data: JobUpdateData): Promise<ScrapeJob> {
    const response = await this.client.put<ScrapeJob>(`/jobs/${id}`, data);
    return response.data;
  }

  async deleteJob(id: string): Promise<void> {
    await this.client.delete(`/jobs/${id}`);
  }

  async runJob(id: string): Promise<JobRunResponse> {
    const response = await this.client.post<JobRunResponse>(`/jobs/${id}/run`);
    return response.data;
  }

  // Results
  async getResults(params?: PaginationParams & { job_id?: string }): Promise<ScrapeResult[]> {
    const response = await this.client.get<ScrapeResult[]>('/results/', { params });
    return response.data;
  }

  async getResult(id: string): Promise<ScrapeResult> {
    const response = await this.client.get<ScrapeResult>(`/results/${id}`);
    return response.data;
  }

  async deleteResult(id: string): Promise<void> {
    await this.client.delete(`/results/${id}`);
  }

  async exportResultCsv(id: string): Promise<Blob> {
    const response = await this.client.get(`/results/${id}/export/csv`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async getJobResults(jobId: string, params?: PaginationParams): Promise<ScrapeResult[]> {
    return this.getResults({ ...params, job_id: jobId });
  }

  async downloadResult(id: string, format: 'json' | 'csv'): Promise<Blob> {
    const response = await this.client.get(`/results/${id}/export/${format}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }
}

export const api = new ApiService();
