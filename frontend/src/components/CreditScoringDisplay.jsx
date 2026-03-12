import React, { useState, useEffect } from 'react';
import { creditScoringService } from '../services/creditScoringService';
import { metricsService } from '../services/metricsService';
import { extractionService } from '../services/extractionService';
import { CreditAnalysisDashboard } from './CreditAnalysisDashboard';

export const CreditScoringDisplay = ({ documentId, entityId, entityName, onScoringComplete }) => {
  const [creditScore, setCreditScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDecisionForm, setShowDecisionForm] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (entityId) {
      loadCreditScore();
    }
  }, [entityId]);

  const loadCreditScore = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await creditScoringService.getEntityCreditScore(entityId);
      setCreditScore(response);
    } catch (err) {
      const statusCode = err?.response?.status;
      if (statusCode === 404) {
        try {
          let targetDocumentId = documentId;
          if (entityId) {
            const extractionRes = await extractionService.getResults(entityId);
            const reviewData = extractionRes?.data;
            if (reviewData?.status === 'approved' && reviewData?.document_id) {
              targetDocumentId = reviewData.document_id;
            }
          }

          const metricsResponse = await metricsService.calculateMetrics(targetDocumentId);
          const financialMetrics = metricsResponse?.extracted_metrics || {};

          const calculated = await creditScoringService.calculateCreditScore({
            entity_id: entityId,
            document_id: targetDocumentId,
            financial_metrics: financialMetrics,
          });

          setCreditScore(calculated);
        } catch (calcErr) {
          setError(calcErr.response?.data?.detail || 'Failed to calculate credit score');
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to load credit score');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  if (!creditScore) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-600">No credit score calculated yet</p>
      </div>
    );
  }

  const riskColor = creditScoringService.getRiskCategoryColor(creditScore.risk_category);
  const riskBadge = creditScoringService.getRiskCategoryBadge(creditScore.risk_category);
  const assessments = creditScoringService.assessmentFromScores(creditScore.component_scores);

  return (
    <div className="space-y-6">
      {/* Main Score Card */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-lg shadow-lg p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <p className="text-sm font-semibold text-slate-300 mb-2">CREDIT SCORE</p>
            <p className="text-5xl font-bold">{creditScore.credit_score}</p>
            <p className="text-sm text-slate-400 mt-2">(Scale: 300-1000)</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-300 mb-2">RISK CATEGORY</p>
            <span className={`inline-block px-4 py-2 rounded-full text-lg font-bold ${riskBadge}`}>
              {creditScore.risk_category.replace(/_/g, ' ')}
            </span>
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-300 mb-2">PROBABILITY OF DEFAULT</p>
            <p className="text-3xl font-bold">{creditScore.probability_of_default.toFixed(2)}%</p>
            <p className="text-sm text-slate-400 mt-2">Annual</p>
          </div>
        </div>
      </div>

      {/* Decision Card */}
      <div className={`rounded-lg shadow p-6 border-l-4 ${
        creditScore.decision === 'APPROVED' ? 'bg-green-50 border-green-500' :
        creditScore.decision === 'DECLINED' ? 'bg-red-50 border-red-500' :
        'bg-yellow-50 border-yellow-500'
      }`}>
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-1">UNDERWRITING DECISION</p>
            <p className="text-xl font-bold" style={{
              color: creditScore.decision === 'APPROVED' ? '#166534' :
                     creditScore.decision === 'DECLINED' ? '#991b1b' :
                     '#92400e'
            }}>
              {creditScoringService.getDecisionDisplay(creditScore.decision)}
            </p>
            <p className="text-sm text-gray-600 mt-2">{creditScore.decision_rationale}</p>
          </div>
          {!creditScore.approved_status && (
            <button
              onClick={() => setShowDecisionForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Record Decision
            </button>
          )}
        </div>
      </div>

      {/* Component Scores Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(creditScore.component_scores).map(([key, score]) => (
          <ComponentScoreCard
            key={key}
            name={key.replace(/_/g, ' ').replace(/score/i, '')}
            score={score}
            assessment={assessments[key]}
          />
        ))}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6 overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'risk-drivers', label: 'Risk Drivers' },
              { id: 'strengths', label: 'Strengths' },
              { id: 'improvements', label: 'Improvements' },
              { id: 'credit-analysis', label: 'Credit Analysis Dashboard' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Credit Score Breakdown</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {Object.entries(creditScore.component_scores).map(([key, score]) => (
                    <div key={key} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-gray-700 font-medium">{key.replace(/_/g, ' ').toUpperCase()}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(score / 100) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-gray-900 font-bold w-10 text-right">{score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {creditScore.recommended_conditions && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3">Recommended Conditions</h4>
                  <ul className="space-y-2">
                    {creditScore.recommended_conditions.map((condition, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                        <span className="text-blue-600 font-bold">•</span>
                        <span>{condition}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Risk Drivers Tab */}
          {activeTab === 'risk-drivers' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900 mb-4">Primary Risk Factors</h4>
              {creditScore.primary_risk_drivers && creditScore.primary_risk_drivers.length > 0 ? (
                <div className="space-y-3">
                  {creditScore.primary_risk_drivers.map((driver, idx) => (
                    <div key={idx} className="p-4 border border-red-200 bg-red-50 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-red-900">{driver.factor}</p>
                          <p className="text-sm text-red-700 mt-1">Score: {driver.score}/100</p>
                        </div>
                        <span className="px-2 py-1 bg-red-200 text-red-800 text-xs font-bold rounded">
                          {driver.impact}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No major risk drivers identified</p>
              )}
            </div>
          )}

          {/* Strengths Tab */}
          {activeTab === 'strengths' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900 mb-4">Strength Areas</h4>
              {creditScore.strength_areas && creditScore.strength_areas.length > 0 ? (
                <div className="space-y-3">
                  {creditScore.strength_areas.map((area, idx) => (
                    <div key={idx} className="p-4 border border-green-200 bg-green-50 rounded-lg">
                      <div className="flex justify-between items-center">
                        <p className="font-semibold text-green-900">{area.factor}</p>
                        <span className="text-sm font-bold text-green-700">Score: {area.score}/100</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No strength areas identified</p>
              )}
            </div>
          )}

          {/* Improvements Tab */}
          {activeTab === 'improvements' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900 mb-4">Areas for Improvement</h4>
              {creditScore.improvement_areas && creditScore.improvement_areas.length > 0 ? (
                <div className="space-y-3">
                  {creditScore.improvement_areas.map((area, idx) => (
                    <div key={idx} className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-yellow-900">{area.factor}</p>
                          <p className="text-sm text-yellow-700 mt-1">Current Score: {area.score}/100</p>
                        </div>
                        <span className="text-sm font-bold text-yellow-800">
                          +{area.potential_improvement} potential
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No improvement areas identified</p>
              )}
            </div>
          )}

          {/* Credit Analysis Dashboard Tab */}
          {activeTab === 'credit-analysis' && (
            <CreditAnalysisDashboard
              entityId={entityId}
              entityName={entityName}
            />
          )}
        </div>
      </div>

      {/* Decision Form Modal */}
      {showDecisionForm && (
        <UnderwritingDecisionForm
          creditScoreId={creditScore.id}
          onClose={() => setShowDecisionForm(false)}
          onComplete={() => {
            setShowDecisionForm(false);
            loadCreditScore();
          }}
        />
      )}
    </div>
  );
};

// Helper Components

const ComponentScoreCard = ({ name, score, assessment }) => {
  const getColor = (score) => {
    if (score >= 80) return 'text-green-700';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBgColor = (score) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-blue-50';
    if (score >= 40) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  return (
    <div className={`rounded-lg p-4 ${getBgColor(score)}`}>
      <p className="text-xs font-semibold text-gray-700 uppercase truncate">{name}</p>
      <p className={`text-2xl font-bold mt-2 ${getColor(score)}`}>{score}</p>
      <p className="text-xs text-gray-600 mt-1">{assessment}</p>
    </div>
  );
};

const UnderwritingDecisionForm = ({ creditScoreId, onClose, onComplete }) => {
  const [formData, setFormData] = useState({
    decision: 'APPROVED',
    decision_reason: '',
    proposed_interest_rate: undefined,
    proposed_loan_amount: undefined,
    approval_conditions: [],
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      await creditScoringService.createUnderwritingDecision({
        credit_score_id: creditScoreId,
        ...formData,
      });
      onComplete();
    } catch (err) {
      setError('Failed to save decision');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full">
        <div className="flex justify-between items-center p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Record Underwriting Decision</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Decision</label>
            <select
              value={formData.decision}
              onChange={(e) => setFormData({ ...formData, decision: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option>APPROVED</option>
              <option>APPROVED_WITH_CONDITIONS</option>
              <option>PENDING_REVIEW</option>
              <option>DECLINED</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Reason</label>
            <textarea
              value={formData.decision_reason}
              onChange={(e) => setFormData({ ...formData, decision_reason: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              rows={3}
              placeholder="Explain the decision..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">Interest Rate (%)</label>
            <input
              type="number"
              step="0.01"
              value={formData.proposed_interest_rate || ''}
              onChange={(e) => setFormData({ ...formData, proposed_interest_rate: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              placeholder="Annual rate"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {submitting ? 'Saving...' : 'Save Decision'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreditScoringDisplay;
