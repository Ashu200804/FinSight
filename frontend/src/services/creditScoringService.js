import axios from 'axios';

const RAW_API_BASE_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';
const API_BASE_URL = RAW_API_BASE_URL.endsWith('/api') ? RAW_API_BASE_URL : `${RAW_API_BASE_URL}/api`;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const normalizeCreditScoreResponse = (payload) => {
  if (!payload) return payload;

  if (payload.recommendation) {
    return {
      ...payload,
      decision: payload.recommendation.decision,
      decision_rationale: payload.recommendation.rationale,
      recommended_conditions: payload.recommendation.conditions || [],
    };
  }

  return {
    ...payload,
    primary_risk_drivers: payload.primary_risk_drivers || [],
    strength_areas: payload.strength_areas || [],
    improvement_areas: payload.improvement_areas || [],
    recommended_conditions: payload.recommended_conditions || [],
  };
};

export const creditScoringService = {
  /**
   * Calculate credit score for an entity
   * @param {object} scoringData - Scoring request data
   * @returns {Promise} Credit scoring response
   */
  calculateCreditScore: async (scoringData) => {
    try {
      const response = await apiClient.post(`/credit-scoring/calculate`, scoringData);
      return normalizeCreditScoreResponse(response.data);
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get latest credit score for entity
   * @param {number} entityId - Entity ID
   * @returns {Promise} Latest credit score
   */
  getEntityCreditScore: async (entityId) => {
    try {
      const response = await apiClient.get(`/credit-scoring/entity/${entityId}`);
      return normalizeCreditScoreResponse(response.data);
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get historical credit scores for trend analysis
   * @param {number} entityId - Entity ID
   * @param {number} limit - Number of records (1-60)
   * @returns {Promise} Historical scores
   */
  getCreditScoreHistory: async (entityId, limit = 12) => {
    try {
      const response = await apiClient.get(`/credit-scoring/history/${entityId}?limit=${limit}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create underwriting decision
   * @param {object} decisionData - Decision details
   * @returns {Promise} Decision record
   */
  createUnderwritingDecision: async (decisionData) => {
    try {
      const response = await apiClient.post(`/credit-scoring/underwriting-decision`, decisionData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get credit scoring methodology
   * @returns {Promise} Scoring documentation
   */
  getScoringMethodology: async () => {
    try {
      const response = await apiClient.get(`/credit-scoring/scoring-methodology`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get risk category color
   * @param {string} riskCategory - Risk category
   * @returns {string} Tailwind color class
   */
  getRiskCategoryColor: (riskCategory) => {
    const colors = {
      'EXCELLENT': 'text-green-700',
      'VERY_GOOD': 'text-green-600',
      'GOOD': 'text-blue-600',
      'FAIR': 'text-yellow-600',
      'POOR': 'text-orange-600',
      'VERY_POOR': 'text-red-700',
      'UNACCEPTABLE': 'text-red-900',
    };
    return colors[riskCategory] || 'text-gray-600';
  },

  /**
   * Get risk category badge
   * @param {string} riskCategory - Risk category
   * @returns {string} Tailwind badge class
   */
  getRiskCategoryBadge: (riskCategory) => {
    const badges = {
      'EXCELLENT': 'bg-green-100 text-green-800',
      'VERY_GOOD': 'bg-green-100 text-green-800',
      'GOOD': 'bg-blue-100 text-blue-800',
      'FAIR': 'bg-yellow-100 text-yellow-800',
      'POOR': 'bg-orange-100 text-orange-800',
      'VERY_POOR': 'bg-red-100 text-red-800',
      'UNACCEPTABLE': 'bg-red-200 text-red-900',
    };
    return badges[riskCategory] || 'bg-gray-100 text-gray-800';
  },

  /**
   * Get decision indicator
   * @param {string} decision - Decision type
   * @returns {string} Display text
   */
  getDecisionDisplay: (decision) => {
    const displays = {
      'APPROVED': '✓ APPROVED',
      'APPROVED_WITH_CONDITIONS': '✓ APPROVED WITH CONDITIONS',
      'PENDING_REVIEW': '⏳ PENDING REVIEW',
      'DECLINED': '✗ DECLINED',
    };
    return displays[decision] || decision;
  },

  /**
   * Get rate adjustment display
   * @param {number} basisPoints - Adjustment in BPS
   * @returns {string} Formatted display
   */
  getFormattedRateAdjustment: (basisPoints) => {
    if (!basisPoints) return 'Base Rate';
    const percentAdjustment = basisPoints / 100;
    if (basisPoints > 0) {
      return `+${basisPoints}bps (+${percentAdjustment.toFixed(2)}%)`;
    }
    return `${basisPoints}bps (${percentAdjustment.toFixed(2)}%)`;
  },

  /**
   * Format probability of default
   * @param {number} pd - Probability (0-100)
   * @returns {string} Formatted
   */
  formatPD: (pd) => {
    return `${pd.toFixed(2)}%`;
  },

  /**
   * Get assessment from component scores
   * @param {object} scores - Component scores object
   * @returns {object} Individual assessments
   */
  assessmentFromScores: (scores) => {
    const assess = (score) => {
      if (score >= 80) return 'Strong';
      if (score >= 65) return 'Adequate';
      if (score >= 50) return 'Weak';
      return 'Critical';
    };
    
    return {
      financial_strength: assess(scores.financial_strength),
      bank_relationship: assess(scores.bank_relationship),
      industry_risk: assess(scores.industry_risk),
      management_quality: assess(scores.management_quality),
      collateral_strength: assess(scores.collateral_strength),
      legal_risk: assess(scores.legal_risk),
      fraud_risk: assess(scores.fraud_risk),
      credit_bureau_score: assess(scores.credit_bureau_score),
    };
  },

  /**
   * Get recommendations for entity based on credit score
   * @param {number} entityId - Entity ID
   * @returns {Promise} Recommendations object
   */
  getRecommendations: async (entityId) => {
    try {
      const response = await apiClient.get(`/credit-scoring/recommendations/${entityId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Get scoring methodology and component details
   * @returns {Promise} Methodology documentation
   */
  getScoringMethodology: async () => {
    try {
      const response = await apiClient.get(`/credit-scoring/scoring-methodology`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Create or update underwriting decision
   * @param {object} decisionData - Decision details
   * @returns {Promise} Decision record
   */
  createUnderwritingDecision: async (decisionData) => {
    try {
      const response = await apiClient.post(`/credit-scoring/underwriting-decision`, decisionData);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

export default creditScoringService;
