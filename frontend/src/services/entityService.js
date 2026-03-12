import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const entityService = {
  createEntity: (data) => apiClient.post('/entity/create', data),
  getEntity: (entityId) => apiClient.get(`/entity/${entityId}`),
  getLatestEntity: () => apiClient.get('/entity/latest'),
  updateEntity: (entityId, data) => apiClient.put(`/entity/${entityId}`, data),
};

export default apiClient;
