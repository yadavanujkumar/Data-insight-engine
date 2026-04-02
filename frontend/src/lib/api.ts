import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Types
export interface Dataset {
  id: number;
  name: string;
  description?: string;
  file_type?: string;
  row_count?: number;
  column_count?: number;
  quality_score?: number;
  status: string;
  created_at: string;
}

export interface QualityScore {
  overall_score: number;
  completeness: number;
  consistency: number;
  validity: number;
  uniqueness: number;
  column_profiles: Record<string, unknown>;
  issues: Array<{ column: string; issue: string; severity: string; detail: string }>;
}

export interface ForecastPoint {
  step: number;
  value: number;
  lower: number;
  upper: number;
}

export interface ForecastResult {
  dataset_id: number;
  target_column: string;
  horizon: number;
  predictions: ForecastPoint[];
  model_used: string;
  metrics?: Record<string, number>;
}

export interface Recommendation {
  id: number;
  title: string;
  description?: string;
  category?: string;
  priority: string;
  expected_impact: number;
  status: string;
  created_at: string;
}

export interface Alert {
  id: number;
  name: string;
  description?: string;
  severity: string;
  status: string;
  metric_name: string;
  threshold_value: number;
  current_value?: number;
  triggered_at?: string;
  created_at: string;
}

export interface MetricSummary {
  metric_name: string;
  count: number;
  avg: number;
  max: number;
  min: number;
}

export interface NLQResponse {
  query: string;
  interpretation: string;
  result?: unknown;
  explanation: string;
}

// API functions
export const datasetsApi = {
  list: () => api.get<Dataset[]>('/datasets'),
  get: (id: number) => api.get<Dataset>(`/datasets/${id}`),
  upload: (file: File, name?: string, description?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (name) form.append('name', name);
    if (description) form.append('description', description);
    return api.post<Dataset>('/datasets/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  preview: (id: number, rows = 10) => api.get(`/datasets/${id}/preview?rows=${rows}`),
  delete: (id: number) => api.delete(`/datasets/${id}`),
};

export const qualityApi = {
  getScore: (datasetId: number) => api.get<QualityScore>(`/quality/${datasetId}`),
  getProfile: (datasetId: number) => api.get(`/quality/${datasetId}/profile`),
};

export const forecastingApi = {
  run: (params: {
    dataset_id: number;
    target_column: string;
    date_column: string;
    horizon: number;
  }) => api.post<ForecastResult>('/forecasting/run', params),
  history: (datasetId: number) => api.get(`/forecasting/history/${datasetId}`),
};

export const recommendationsApi = {
  list: () => api.get<Recommendation[]>('/recommendations'),
  generate: (datasetId: number) => api.post<Recommendation[]>(`/recommendations/generate/${datasetId}`),
  update: (id: number, status: string) => api.patch<Recommendation>(`/recommendations/${id}`, { status }),
};

export const alertsApi = {
  list: (status?: string) => api.get<Alert[]>(`/alerts${status ? `?status=${status}` : ''}`),
  create: (data: { name: string; metric_name: string; threshold_value: number; severity: string }) =>
    api.post<Alert>('/alerts', data),
  resolve: (id: number) => api.patch<Alert>(`/alerts/${id}/resolve`),
};

export const metricsApi = {
  list: () => api.get<MetricSummary[]>('/metrics'),
  history: (name: string, limit = 50) => api.get(`/metrics/${name}?limit=${limit}`),
  record: (name: string, value: number) =>
    api.post('/metrics/record', { metric_name: name, metric_value: value }),
};

export const nlqApi = {
  query: (query: string, dataset_id?: number) =>
    api.post<NLQResponse>('/nlq/query', { query, dataset_id }),
};

export const analyticsApi = {
  kpis: (datasetId: number) => api.get(`/analytics/${datasetId}/kpis`),
  run: (params: { dataset_id: number; target_column: string; operations: string[] }) =>
    api.post('/analytics/run', params),
};

export const cleaningApi = {
  run: (params: { dataset_id: number; operations: string[] }) =>
    api.post('/cleaning/run', params),
};

export const simulationApi = {
  run: (params: {
    dataset_id: number;
    target_column: string;
    parameters: Record<string, unknown>;
    n_simulations: number;
  }) => api.post('/simulation/run', params),
};

export default api;
