import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';

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

export const aiExtractionService = {
  processDocument: (file, entityId, documentType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('entity_id', entityId);
    formData.append('document_type', documentType);

    return axios.post(`${API_BASE_URL}/ai/extract/process-document`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },

  processStoredDocument: (documentId) => 
    apiClient.get(`/ai/extract/process-document/${documentId}`),

  batchProcessDocuments: (entityId) => 
    apiClient.post(`/ai/extract/batch-process?entity_id=${entityId}`),

  getPipelineInfo: () => 
    apiClient.get('/ai/extract/pipeline-info'),
};

export default apiClient;
