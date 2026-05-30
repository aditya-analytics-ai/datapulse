import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

// Auto-attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dp_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Token expiry interceptor — redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isAuthRoute = error.config?.url?.includes('/api/auth/');
      if (!isAuthRoute) {
        localStorage.removeItem('dp_token');
        localStorage.removeItem('dp_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const loginUser = (email, password) =>
  api.post('/api/auth/login', { email, password });

export const registerUser = (name, email, password) =>
  api.post('/api/auth/register', { name, email, password });

// Health check
export const checkHealth = () => api.get('/health');

// Scraper
export const scrapeUrl = (url, force_playwright = false) =>
  api.post('/api/scrape', { url, force_playwright });

// Jobs (history)
export const getAllJobs = (params) => api.get('/api/jobs', { params });
export const getJobById = (id) => api.get(`/api/jobs/${id}`);
export const deleteJob = (id) => api.delete(`/api/jobs/${id}`);

// Export
export const getExportUrl = (id, format) =>
  `${BASE_URL}/api/export/${id}/${format}`;

// Job Market
export const getJobMarket = (category, limit) =>
  api.get('/api/jobs/market', { params: { category, limit } });

export const getJobMarketExportUrl = (id) =>
  `${BASE_URL}/api/jobs/market/export/${id}/excel`;

export default api;
