import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const extractionService = {
  /**
   * GET /extraction/results/{entityId}
   * Returns ExtractionResultResponse with sections of extracted fields.
   */
  getResults: (entityId) =>
    apiClient.get(`/extraction/results/${entityId}`),

  /**
   * POST /extraction/approve
   * Saves corrections and marks the result as approved or rejected.
   *
   * @param {object} payload
   *   {entity_id, result_id?, corrected_fields, review_notes, status}
   */
  approve: (payload) =>
    apiClient.post('/extraction/approve', payload),
};

export default extractionService;
