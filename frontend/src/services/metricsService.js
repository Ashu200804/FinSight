import axios from 'axios';

const RAW_API_BASE_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';
const API_BASE_URL = RAW_API_BASE_URL.endsWith('/api') ? RAW_API_BASE_URL : `${RAW_API_BASE_URL}/api`;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const metricsService = {
  /**
   * Calculate financial metrics for a document
   * @param {number} documentId - ID of the document to analyze
   * @param {boolean} useExtractedData - Whether to use AI-extracted data
   * @returns {Promise} Financial metrics response
   */
  calculateMetrics: async (documentId, useExtractedData = true) => {
    try {
      const response = await apiClient.post(`/metrics/calculate`, {
        document_id: documentId,
        use_extracted_data: useExtractedData,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get historical metrics for an entity
   * @param {number} entityId - ID of the entity
   * @param {number} limit - Number of recent metrics to retrieve (1-100)
   * @returns {Promise} List of historical metrics
   */
  getEntityMetrics: async (entityId, limit = 10) => {
    try {
      const response = await apiClient.get(
        `/metrics/entity/${entityId}?limit=${limit}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get detailed metrics for a specific document
   * @param {number} documentId - ID of the document
   * @returns {Promise} Complete financial metrics and ratios
   */
  getDocumentMetrics: async (documentId) => {
    try {
      const response = await apiClient.get(
        `/metrics/document/${documentId}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Compare metrics across multiple documents for trend analysis
   * @param {number} entityId - ID of the entity
   * @returns {Promise} Comparative analysis and trend indicators
   */
  compareMetrics: async (entityId) => {
    try {
      const response = await apiClient.get(
        `/metrics/comparison/${entityId}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get information about all available metrics
   * @returns {Promise} Metrics documentation and definitions
   */
  getMetricsInfo: async () => {
    try {
      const response = await apiClient.get(`/metrics/metrics-info`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Format a financial value as Indian Rupee
   * @param {number} value - Value to format
   * @param {boolean} abbreviate - Whether to abbreviate (e.g., 1.5L for lakhs)
   * @returns {string} Formatted value
   */
  formatCurrency: (value, abbreviate = false) => {
    if (!value && value !== 0) return '-';
    
    if (abbreviate) {
      if (value >= 10000000) {
        return `₹${(value / 10000000).toFixed(2)}Cr`;
      } else if (value >= 100000) {
        return `₹${(value / 100000).toFixed(2)}L`;
      }
    }
    
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  },

  /**
   * Format a ratio value with interpretation
   * @param {number} value - Ratio value
   * @param {string} unit - Unit type
   * @returns {string} Formatted ratio
   */
  formatRatio: (value, unit = 'ratio') => {
    if (!value && value !== 0) return '-';
    
    switch (unit) {
      case '%':
        return `${value.toFixed(2)}%`;
      case 'times':
        return `${value.toFixed(2)}x`;
      case 'days':
        return `${Math.round(value)} days`;
      case 'ratio':
      default:
        return value.toFixed(2);
    }
  },

  /**
   * Get score assessment color based on score value
   * @param {number} score - Score value (0-100)
   * @returns {string} Color class name
   */
  getScoreColor: (score) => {
    if (score >= 80) return 'text-green-600'; // Excellent
    if (score >= 60) return 'text-blue-600'; // Good
    if (score >= 40) return 'text-yellow-600'; // Fair
    if (score >= 20) return 'text-orange-600'; // Poor
    return 'text-red-600'; // Very Poor
  },

  /**
   * Get score assessment badge color
   * @param {number} score - Score value (0-100)
   * @returns {string} Badge class name
   */
  getScoreBadgeClass: (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-blue-100 text-blue-800';
    if (score >= 40) return 'bg-yellow-100 text-yellow-800';
    if (score >= 20) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  },

  /**
   * Get risk level color
   * @param {string} riskLevel - Risk level (low, medium, high, very_high)
   * @returns {string} Color class name
   */
  getRiskLevelColor: (riskLevel) => {
    switch (riskLevel) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-orange-600';
      case 'very_high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  },

  /**
   * Get risk level badge
   * @param {string} riskLevel - Risk level
   * @returns {string} Badge class name
   */
  getRiskLevelBadge: (riskLevel) => {
    switch (riskLevel) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'very_high':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  },

  /**
   * Calculate overall health score from component scores
   * @param {object} scores - Object with profitability, liquidity, solvency, efficiency scores
   * @returns {number} Weighted overall score
   */
  calculateOverallScore: (scores) => {
    if (!scores) return 0;
    
    const profitability = scores.profitability || 0;
    const liquidity = scores.liquidity || 0;
    const solvency = scores.solvency || 0;
    const efficiency = scores.efficiency || 0;
    
    return (
      profitability * 0.3 +
      liquidity * 0.25 +
      solvency * 0.25 +
      efficiency * 0.2
    );
  },
};

export default metricsService;
