import axios from 'axios';
import type {
  DashboardKPIs, TrendDataPoint, TopRedFlag,
  BranchSummary, BranchDetail,
  CustomerDetail,
  MisuseOverview, VendorHub,
  Case, CaseCreate, CaseUpdate,
  User
} from '../types';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
  const response = await apiClient.post('/auth/login', { username, password });
  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// Dashboard
export const getDashboardKPIs = async (): Promise<DashboardKPIs> => {
  const response = await apiClient.get('/dashboard/kpis');
  return response.data;
};

export const getDashboardTrend = async (): Promise<TrendDataPoint[]> => {
  const response = await apiClient.get('/dashboard/trend');
  return response.data;
};

export const getTopRedFlags = async (): Promise<TopRedFlag[]> => {
  const response = await apiClient.get('/dashboard/top-red-flags');
  return response.data;
};

// Branches
export const getBranches = async (): Promise<BranchSummary[]> => {
  const response = await apiClient.get('/branches');
  return response.data;
};

export const getBranchDetail = async (branchId: string): Promise<BranchDetail> => {
  const response = await apiClient.get(`/branches/${branchId}`);
  return response.data;
};

// Customers
export const getCustomers = async (params?: {
  search?: string;
  branch_id?: string;
  risk_category?: string;
  page?: number;
  page_size?: number;
}): Promise<{ total: number; page: number; page_size: number; items: any[] }> => {
  const response = await apiClient.get('/customers', { params });
  return response.data;
};

export const getCustomerDetail = async (cif: string): Promise<CustomerDetail> => {
  const response = await apiClient.get(`/customers/${cif}`);
  return response.data;
};

// Misuse
export const getMisuseOverview = async (): Promise<MisuseOverview> => {
  const response = await apiClient.get('/misuse/overview');
  return response.data;
};

export const getMisuseVendorHubs = async (): Promise<VendorHub[]> => {
  const response = await apiClient.get('/misuse/vendor-hubs');
  return response.data;
};

export const getMisuseDetail = async (cif: string): Promise<any> => {
  const response = await apiClient.get(`/misuse/${cif}`);
  return response.data;
};

// Cases
export const getCases = async (params?: {
  status?: string;
  priority?: string;
  assigned_to?: string;
  page?: number;
  page_size?: number;
}): Promise<{ total: number; page: number; page_size: number; items: Case[] }> => {
  const response = await apiClient.get('/cases', { params });
  return response.data;
};

export const createCase = async (data: CaseCreate): Promise<any> => {
  const response = await apiClient.post('/cases', data);
  return response.data;
};

export const updateCase = async (caseId: string, data: CaseUpdate): Promise<any> => {
  const response = await apiClient.put(`/cases/${caseId}`, data);
  return response.data;
};

export const getCaseAuditLog = async (caseId: string): Promise<any> => {
  const response = await apiClient.get(`/cases/${caseId}/audit-log`);
  return response.data;
};

export default apiClient;
