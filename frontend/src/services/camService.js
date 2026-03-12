import axios from 'axios';

const RAW_API_BASE = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';
const API_BASE = RAW_API_BASE.endsWith('/api') ? RAW_API_BASE : `${RAW_API_BASE}/api`;
const CAM_ROOT = API_BASE.endsWith('/api') ? API_BASE.slice(0, -4) : RAW_API_BASE;
const CAM_API = `${CAM_ROOT}/cam`;

const getAuthHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
});

const triggerPdfDownload = (blobData, fallbackFilename) => {
  const url = window.URL.createObjectURL(new Blob([blobData], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fallbackFilename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const camService = {
  async getCamPreview(entityId) {
    const response = await axios.get(`${CAM_API}/preview/${entityId}`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  async generateCam(entityId) {
    const response = await axios.get(`${CAM_API}/generate/${entityId}`, {
      headers: getAuthHeader(),
      responseType: 'blob',
    });

    const contentDisposition = response.headers['content-disposition'] || '';
    const match = contentDisposition.match(/filename="?([^\"]+)"?/);
    const filename = match?.[1] || `CAM_Report_Entity_${entityId}.pdf`;

    triggerPdfDownload(response.data, filename);

    return { success: true, filename };
  },

  async getCamHistory(entityId) {
    const response = await axios.get(`${CAM_API}/history/${entityId}`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  async downloadStoredCam(reportId) {
    const response = await axios.get(`${CAM_API}/download/${reportId}`, {
      headers: getAuthHeader(),
      responseType: 'blob',
    });

    const contentDisposition = response.headers['content-disposition'] || '';
    const match = contentDisposition.match(/filename="?([^\"]+)"?/);
    const filename = match?.[1] || `CAM_Report_${reportId}.pdf`;

    triggerPdfDownload(response.data, filename);
  },
};

export default camService;
