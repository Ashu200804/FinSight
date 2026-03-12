/**
 * Research Service
 * 
 * Frontend service layer for research engine API calls
 */

import axios from 'axios';

const RAW_API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';
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

export const researchService = {
  /**
   * Search for news articles about company
   * @param {object} request - Search request
   * @returns {Promise} News search results
   */
  searchCompanyNews: async (request) => {
    try {
      const response = await apiClient.post(`/research/news/search`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Detect legal risks for company
   * @param {object} request - Legal risk detection request
   * @returns {Promise} Legal risks and compliance status
   */
  detectLegalRisks: async (request) => {
    try {
      const response = await apiClient.post(`/research/legal/detect-risks`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Analyze market sentiment for company
   * @param {object} request - Sentiment analysis request
   * @returns {Promise} Market sentiment analysis
   */
  analyzeMarketSentiment: async (request) => {
    try {
      const response = await apiClient.post(`/research/sentiment/analyze`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Gather industry intelligence
   * @param {object} request - Industry intelligence request
   * @returns {Promise} Industry reports and market data
   */
  gatherIndustryIntelligence: async (request) => {
    try {
      const response = await apiClient.post(`/research/industry/intelligence`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Generate comprehensive research report
   * @param {object} request - Comprehensive research request
   * @returns {Promise} Full research report combining all sources
   */
  generateComprehensiveResearch: async (request) => {
    try {
      const response = await apiClient.post(`/research/comprehensive`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get latest research report for entity
   * @param {number} entityId - Entity ID
   * @returns {Promise} Latest research report
   */
  getEntityLatestReport: async (entityId) => {
    try {
      const response = await apiClient.get(`/research/entity/${entityId}/latest-report`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get news articles for entity
   * @param {number} entityId - Entity ID
   * @param {number} days - Number of days to look back
   * @param {number} limit - Max articles to return
   * @returns {Promise} List of news articles
   */
  getEntityNews: async (entityId, days = 30, limit = 20) => {
    try {
      const response = await apiClient.get(`/research/entity/${entityId}/news?days=${days}&limit=${limit}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get legal risks for entity
   * @param {number} entityId - Entity ID
   * @returns {Promise} List of legal risks
   */
  getEntityLegalRisks: async (entityId) => {
    try {
      const response = await apiClient.get(`/research/entity/${entityId}/legal-risks`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get market sentiment for entity
   * @param {number} entityId - Entity ID
   * @returns {Promise} Market sentiment data
   */
  getEntitySentiment: async (entityId) => {
    try {
      const response = await apiClient.get(`/research/entity/${entityId}/sentiment`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create research task
   * @param {object} taskData - Task configuration
   * @returns {Promise} Created task details
   */
  createResearchTask: async (taskData) => {
    try {
      const response = await apiClient.post(`/research/tasks`, taskData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get research task status
   * @param {number} taskId - Task ID
   * @returns {Promise} Task status and results
   */
  getResearchTask: async (taskId) => {
    try {
      const response = await apiClient.get(`/research/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create bulk research tasks
   * @param {object} request - Bulk research request
   * @returns {Promise} Created task IDs
   */
  createBulkResearch: async (request) => {
    try {
      const response = await apiClient.post(`/research/bulk`, request);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get sentiment color class
   * @param {string} sentiment - Sentiment value
   * @returns {string} Tailwind color class
   */
  getSentimentColor: (sentiment) => {
    const colors = {
      POSITIVE: 'text-green-700',
      NEGATIVE: 'text-red-700',
      NEUTRAL: 'text-gray-700'
    };
    return colors[sentiment] || 'text-gray-700';
  },

  /**
   * Get sentiment badge class
   * @param {string} sentiment - Sentiment value
   * @returns {string} Tailwind badge class
   */
  getSentimentBadge: (sentiment) => {
    const badges = {
      POSITIVE: 'bg-green-100 text-green-800',
      NEGATIVE: 'bg-red-100 text-red-800',
      NEUTRAL: 'bg-gray-100 text-gray-800'
    };
    return badges[sentiment] || 'bg-gray-100 text-gray-800';
  },

  /**
   * Format research report rating
   * @param {string} rating - Rating value
   * @returns {string} Formatted rating with icon
   */
  formatRating: (rating) => {
    const ratings = {
      EXCELLENT: '⭐⭐⭐⭐⭐ Excellent',
      GOOD: '⭐⭐⭐⭐ Good',
      FAIR: '⭐⭐⭐ Fair',
      POOR: '⭐⭐ Poor',
      CRITICAL: '⭐ Critical'
    };
    return ratings[rating] || rating;
  },

  /**
   * Format reliability score as percentage
   * @param {number} score - Score from 0-1
   * @returns {string} Formatted percentage
   */
  formatReliability: (score) => {
    return `${(score * 100).toFixed(1)}%`;
  }
};

export default researchService;
