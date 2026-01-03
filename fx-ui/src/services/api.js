import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
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

// Health
export const checkHealth = () => API.get('/api/v1/fx/health');

// Routing APIs
export const getTreasuryRates = () => API.get('/api/v1/fx/routing/treasury-rates');
export const getCustomerTiers = () => API.get('/api/v1/fx/routing/customer-tiers');
export const getProviders = () => API.get('/api/v1/fx/routing/providers');
export const getEffectiveRate = (pair, params) => API.get(`/api/v1/fx/routing/effective-rate/${pair}`, { params });
export const recommendRoute = (params) => API.post('/api/v1/fx/routing/recommend', null, { params });

// Multi-rail APIs (CBDC + Stablecoin)
export const getCBDCs = () => API.get('/api/v1/fx/multi-rail/cbdc');
export const getStablecoins = () => API.get('/api/v1/fx/multi-rail/stablecoins');
export const getMultiRailRoute = (params) => API.post('/api/v1/fx/multi-rail/route', null, { params });

// Deals APIs
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

// Pricing APIs
export const getPricingQuote = (data) => API.post('/api/v1/fx/pricing/quote', data);
export const getSegments = () => API.get('/api/v1/fx/pricing/segments');
export const getTiers = () => API.get('/api/v1/fx/pricing/tiers');

// Chat API
export const sendChatMessage = (message) => API.post('/api/v1/fx/chat', { message });

// Admin APIs for reference tables
export const listAdminResources = () => API.get('/api/v1/fx/admin/resources');
export const getAdminResource = (resourceType) => API.get(`/api/v1/fx/admin/${resourceType}`);
export const getAdminResourceItem = (resourceType, itemId) => API.get(`/api/v1/fx/admin/${resourceType}/${itemId}`);
export const createAdminResource = (resourceType, data) => API.post(`/api/v1/fx/admin/${resourceType}`, data);
export const updateAdminResource = (resourceType, itemId, data) => API.put(`/api/v1/fx/admin/${resourceType}/${itemId}`, data);
export const deleteAdminResource = (resourceType, itemId) => API.delete(`/api/v1/fx/admin/${resourceType}/${itemId}`);
export const reloadAdminResource = (resourceType) => API.post(`/api/v1/fx/admin/${resourceType}/reload`);

export default API;
