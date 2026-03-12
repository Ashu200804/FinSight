/**
 * Explainability Service
 * 
 * Frontend service layer for explainability API endpoints.
 * Handles SHAP-based explanation generation and retrieval.
 */

import axios from 'axios';

const RAW_API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:9052';
const API_BASE = RAW_API_BASE.endsWith('/api') ? RAW_API_BASE : `${RAW_API_BASE}/api`;
const EXPLAINABILITY_API = `${API_BASE}/explainability`;

const getAuthHeader = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
});

// Helper functions
export const getRatingColor = (rating) => {
  const colors = {
    'AAA': 'text-green-700 bg-green-50',
    'AA': 'text-green-600 bg-green-50',
    'A': 'text-blue-700 bg-blue-50',
    'BBB': 'text-yellow-700 bg-yellow-50',
    'BB': 'text-orange-600 bg-orange-50',
    'B': 'text-orange-700 bg-orange-50',
    'CCC': 'text-red-600 bg-red-50',
    'D': 'text-red-700 bg-red-50'
  };
  return colors[rating] || 'text-gray-700 bg-gray-50';
};

export const getSeverityColor = (severity) => {
  const colors = {
    'CRITICAL': 'bg-red-600 text-white',
    'HIGH': 'bg-orange-600 text-white',
    'MEDIUM': 'bg-yellow-600 text-white',
    'LOW': 'bg-blue-600 text-white'
  };
  return colors[severity] || 'bg-gray-600 text-white';
};

export const getImpactColor = (impact) => {
  const colors = {
    'CRITICAL': 'bg-red-100 text-red-800 border-red-300',
    'HIGH': 'bg-orange-100 text-orange-800 border-orange-300',
    'MEDIUM': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'LOW': 'bg-blue-100 text-blue-800 border-blue-300'
  };
  return colors[impact] || 'bg-gray-100 text-gray-800 border-gray-300';
};

export const getDirectionColor = (direction) => {
  const colors = {
    'POSITIVE': 'text-green-600',
    'NEGATIVE': 'text-red-600',
    'NEUTRAL': 'text-gray-600'
  };
  return colors[direction] || 'text-gray-600';
};

export const getDirectionIcon = (direction) => {
  const icons = {
    'POSITIVE': '↑',
    'NEGATIVE': '↓',
    'NEUTRAL': '→'
  };
  return icons[direction] || '→';
};

export const explainabilityService = {
  /**
   * Generate explanation for a credit decision
   * POST /api/explainability/explain-decision
   */
  async explainDecision(request) {
    try {
      const response = await axios.post(
        `${EXPLAINABILITY_API}/explain-decision`,
        request,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error explaining decision:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to generate explanation',
        status: error.response?.status
      };
    }
  },

  /**
   * Get stored explanation by ID
   * GET /api/explainability/explanation/{id}
   */
  async getExplanation(explanationId) {
    try {
      const response = await axios.get(
        `${EXPLAINABILITY_API}/explanation/${explanationId}`,
        {
          headers: getAuthHeader()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error retrieving explanation:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to retrieve explanation',
        status: error.response?.status
      };
    }
  },

  /**
   * Get latest explanation for an entity
   * GET /api/explainability/entity/{id}/latest-explanation
   */
  async getLatestExplanation(entityId) {
    try {
      const response = await axios.get(
        `${EXPLAINABILITY_API}/entity/${entityId}/latest-explanation`,
        {
          headers: getAuthHeader()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error retrieving latest explanation:', error);
      // Return null if explanation doesn't exist
      if (error.response?.status === 404) {
        return null;
      }
      throw {
        message: error.response?.data?.detail || 'Failed to retrieve latest explanation',
        status: error.response?.status
      };
    }
  },

  /**
   * Perform sensitivity analysis
   * POST /api/explainability/sensitivity-analysis
   */
  async sensitivityAnalysis(request) {
    try {
      const response = await axios.post(
        `${EXPLAINABILITY_API}/sensitivity-analysis`,
        request,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error performing sensitivity analysis:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to perform sensitivity analysis',
        status: error.response?.status
      };
    }
  },

  /**
   * Get feature importance for entity
   * GET /api/explainability/feature-importance/{id}
   */
  async getFeatureImportance(entityId, limit = 10) {
    try {
      const response = await axios.get(
        `${EXPLAINABILITY_API}/feature-importance/${entityId}?limit=${limit}`,
        {
          headers: getAuthHeader()
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error retrieving feature importance:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to retrieve feature importance',
        status: error.response?.status
      };
    }
  },

  /**
   * Analyze risk factors
   * POST /api/explainability/risk-factor-analysis
   */
  async analyzeRiskFactors(request) {
    try {
      const response = await axios.post(
        `${EXPLAINABILITY_API}/risk-factor-analysis`,
        request,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error analyzing risk factors:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to analyze risk factors',
        status: error.response?.status
      };
    }
  },

  /**
   * Generate batch explanations
   * POST /api/explainability/batch-explanations
   */
  async batchExplanations(request) {
    try {
      const response = await axios.post(
        `${EXPLAINABILITY_API}/batch-explanations`,
        request,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating batch explanations:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to generate batch explanations',
        status: error.response?.status
      };
    }
  },

  /**
   * Generate SWOT analysis
   * POST /api/explainability/swot-analysis
   */
  async generateSwotAnalysis(request) {
    try {
      const response = await axios.post(
        `${EXPLAINABILITY_API}/swot-analysis`,
        request,
        {
          headers: {
            ...getAuthHeader(),
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating SWOT analysis:', error);
      throw {
        message: error.response?.data?.detail || 'Failed to generate SWOT analysis',
        status: error.response?.status
      };
    }
  },

  /**
   * Health check
   * GET /api/explainability/health
   */
  async healthCheck() {
    try {
      const response = await axios.get(`${EXPLAINABILITY_API}/health`);
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unhealthy' };
    }
  }
};

// Export helper function to format explanation data
export function formatExplanation(explanation) {
  return {
    ...explanation,
    scorePercentage: (explanation.final_score / 10).toFixed(1),
    decisionLabel: {
      'APPROVE': 'Approved',
      'CONDITIONAL_APPROVE': 'Conditional Approval',
      'DECLINE': 'Declined'
    }[explanation.decision] || explanation.decision,
    confidencePercentage: (explanation.decision_confidence * 100).toFixed(1),
    explanationConfidencePercentage: (explanation.explanation_confidence * 100).toFixed(0)
  };
}
