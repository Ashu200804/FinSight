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

export const documentService = {
  uploadDocument: (file, entityId, documentType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('entity_id', entityId);
    formData.append('document_type', documentType);

    return axios.post(`${API_BASE_URL}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
  },

  getEntityDocuments: (entityId) => apiClient.get(`/documents/entity/${entityId}`),
  
  downloadDocument: (documentId) => 
    apiClient.get(`/documents/${documentId}/download`, { responseType: 'blob' }),
  
  deleteDocument: (documentId) => apiClient.delete(`/documents/${documentId}`),
  
  getDocumentVersions: (documentId) => apiClient.get(`/documents/${documentId}/versions`),

  getDocumentPreview: (documentId) => apiClient.get(`/documents/preview/${documentId}`),

  getSupportedDocumentTypes: () => apiClient.get('/documents/supported-types'),
};

export default apiClient;

