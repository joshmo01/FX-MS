import axios from 'axios';

const API = axios.create({ 
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for debugging
API.interceptors.response.use(
  response => {
    console.log('API Response:', response.config.url, response.data);
    return response;
  },
  error => {
    console.error('API Error:', error.config?.url, error.message);
    return Promise.reject(error);
  }
);

export const checkHealth = () => API.get('/api/v1/fx/health');
export const getTreasuryRates = () => API.get('/api/v1/fx/routing/treasury-rates');
export const getCustomerTiers = () => API.get('/api/v1/fx/routing/customer-tiers');
export const getProviders = () => API.get('/api/v1/fx/routing/providers');
export const getCBDCs = () => API.get('/api/v1/fx/multi-rail/cbdc');
export const getStablecoins = () => API.get('/api/v1/fx/multi-rail/stablecoins');
export const getDeals = (params) => API.get('/api/v1/fx/deals', { params });
export const getDeal = (id) => API.get(`/api/v1/fx/deals/${id}`);
export const createDeal = (data) => API.post('/api/v1/fx/deals', data);
export const submitDeal = (id, data) => API.post(`/api/v1/fx/deals/${id}/submit`, data);
export const approveDeal = (id, data) => API.post(`/api/v1/fx/deals/${id}/approve`, data);
export const rejectDeal = (id, data) => API.post(`/api/v1/fx/deals/${id}/reject`, data);
export const utilizeDeal = (id, data) => API.post(`/api/v1/fx/deals/${id}/utilize`, data);
export const getDealUtilizations = (id) => API.get(`/api/v1/fx/deals/${id}/utilizations`);
export const getDealAuditLog = (id) => API.get(`/api/v1/fx/deals/${id}/audit-log`);
export const getActiveDeals = (params) => API.get('/api/v1/fx/deals/active', { params });
export const getBestRate = (params) => API.get('/api/v1/fx/deals/best-rate', { params });

export default API;
