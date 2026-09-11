import axios from 'axios';
import {
  AuthResponse,
  User,
  DocumentItem,
  QueryResult,
  EvaluationListItem,
  EvaluationDetail,
  DashboardStats,
  DashboardCharts,
  UserSettings
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Attach JWT Bearer token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 Unauthorized globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('current_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await api.post<AuthResponse>('/auth/login', { email, password });
    return res.data;
  },
  register: async (name: string, email: string, password: string): Promise<AuthResponse> => {
    const res = await api.post<AuthResponse>('/auth/register', { name, email, password });
    return res.data;
  },
  getCurrentUser: async (): Promise<User> => {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
};

export const documentApi = {
  uploadDocument: async (
    file: File,
    chunkSize?: number,
    chunkOverlap?: number,
    onProgress?: (percent: number) => void
  ): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);
    if (chunkSize) formData.append('chunk_size', chunkSize.toString());
    if (chunkOverlap) formData.append('chunk_overlap', chunkOverlap.toString());

    const res = await api.post<DocumentItem>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  },
  getDocuments: async (): Promise<DocumentItem[]> => {
    const res = await api.get<DocumentItem[]>('/documents');
    return res.data;
  },
  getDocumentDetail: async (id: string): Promise<DocumentItem> => {
    const res = await api.get<DocumentItem>(`/documents/${id}`);
    return res.data;
  },
  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },
  reprocessDocument: async (id: string): Promise<DocumentItem> => {
    const res = await api.post<DocumentItem>(`/documents/${id}/reprocess`);
    return res.data;
  },
};

export const ragApi = {
  query: async (
    question: string,
    documentIds?: string[],
    topK?: number,
    temperature?: number
  ): Promise<QueryResult> => {
    const res = await api.post<QueryResult>('/query', {
      question,
      document_ids: documentIds,
      top_k: topK,
      temperature,
    });
    return res.data;
  },
  getQueryById: async (id: string): Promise<QueryResult> => {
    const res = await api.get<QueryResult>(`/query/${id}`);
    return res.data;
  },
};

export const evaluationApi = {
  evaluateDirect: async (
    question: string,
    answer: string,
    context: string
  ): Promise<QueryResult> => {
    const res = await api.post<QueryResult>('/evaluate', { question, answer, context });
    return res.data;
  },
  getEvaluations: async (search?: string, status?: string): Promise<EvaluationListItem[]> => {
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (status && status !== 'ALL') params.status = status;
    const res = await api.get<EvaluationListItem[]>('/evaluations', { params });
    return res.data;
  },
  getEvaluationDetail: async (id: string): Promise<EvaluationDetail> => {
    const res = await api.get<EvaluationDetail>(`/evaluations/${id}`);
    return res.data;
  },
};

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const res = await api.get<DashboardStats>('/dashboard/stats');
    return res.data;
  },
  getCharts: async (): Promise<DashboardCharts> => {
    const res = await api.get<DashboardCharts>('/dashboard/charts');
    return res.data;
  },
};

export const settingsApi = {
  getSettings: async (): Promise<UserSettings> => {
    const res = await api.get<UserSettings>('/settings');
    return res.data;
  },
  updateSettings: async (settings: Partial<UserSettings> & { custom_api_key?: string }): Promise<UserSettings> => {
    const res = await api.put<UserSettings>('/settings', settings);
    return res.data;
  },
};

export default api;
