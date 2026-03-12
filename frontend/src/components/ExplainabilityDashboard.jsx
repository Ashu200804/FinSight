/**
 * ExplainabilityDashboard Component
 * 
 * Displays SHAP-based explanations for credit decisions with:
 * - Feature importance ranking
 * - Top contributing factors
 * - Risk factor analysis
 * - Sensitivity analysis
 * - Human-readable reasoning
 */

import React, { useState, useEffect } from 'react';
import { explainabilityService } from '@/services/explainabilityService';
import { metricsService } from '../services/metricsService';
import { creditScoringService } from '../services/creditScoringService';
import { extractionService } from '../services/extractionService';

export function ExplainabilityDashboard({ entityId, entityName, creditDecisionId, onClose }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [sensitivity, setSensitivity] = useState(null);
  const [swotData, setSwotData] = useState(null);
  const [swotLoading, setSwotLoading] = useState(false);
  const [swotError, setSwotError] = useState(null);

  useEffect(() => {
    if (entityId) {
      loadExplanation();
    }
  }, [entityId, creditDecisionId]);

  const mapScoreToRating = (score) => {
    if (score >= 900) return 'AAA';
    if (score >= 850) return 'AA';
    if (score >= 780) return 'A';
    if (score >= 720) return 'BBB';
    if (score >= 660) return 'BB';
    if (score >= 600) return 'B';
    if (score >= 540) return 'CCC';
    return 'D';
  };

  const mapDecision = (decision) => {
    const normalized = String(decision || '').toUpperCase();
    if (normalized.includes('DECLINE')) return 'DECLINE';
    if (normalized.includes('CONDITION')) return 'CONDITIONAL_APPROVE';
    return 'APPROVE';
  };

  const normalizeMetrics = (sourceMetrics = {}) => {
    const normalized = {};
    Object.entries(sourceMetrics).forEach(([key, value]) => {
      const numeric = Number(value);
      if (Number.isFinite(numeric)) {
        normalized[key] = numeric;
      }
    });
    return normalized;
  };

  const loadExplanation = async () => {
    try {
      setLoading(true);
      setError(null);

      let liveExplanation = await explainabilityService.getLatestExplanation(entityId);

      if (!liveExplanation) {
        const [extractionResult, latestCreditScore] = await Promise.all([
          extractionService.getResults(entityId),
          creditScoringService.getEntityCreditScore(entityId),
        ]);

        const targetDocumentId = extractionResult?.data?.document_id;
        if (!targetDocumentId) {
          throw new Error('No processed extraction found for this entity. Process documents first, then open Explainability.');
        }

        const metricsResponse = await metricsService.calculateMetrics(targetDocumentId);
        const latestMetrics = metricsResponse?.extracted_metrics;
        if (!latestMetrics) {
          throw new Error('No financial metrics found for this entity. Calculate metrics first, then open Explainability.');
        }
        if (!latestCreditScore?.credit_score) {
          throw new Error('No credit score found for this entity. Run credit scoring first, then open Explainability.');
        }

        const normalizedMetrics = normalizeMetrics(latestMetrics);
        const featureNames = Object.keys(normalizedMetrics);

        if (featureNames.length === 0) {
          throw new Error('Financial metrics are present but not numeric. Recalculate metrics before generating explainability.');
        }

        const request = {
          entity_id: entityId,
          credit_score: Number(latestCreditScore.credit_score),
          credit_rating: mapScoreToRating(Number(latestCreditScore.credit_score)),
          decision: mapDecision(latestCreditScore.decision),
          features: normalizedMetrics,
          feature_names: featureNames,
          metrics: normalizedMetrics,
          model_version: '1.0',
          model_type: 'xgboost',
        };

        liveExplanation = await explainabilityService.explainDecision(request);
      }

      setExplanation(liveExplanation);
      await loadSwotAnalysis(liveExplanation);
    } catch (err) {
      setError(err.message || 'Failed to load explanation');
    } finally {
      setLoading(false);
    }
  };

  const loadSwotAnalysis = async (explanationData) => {
    try {
      setSwotLoading(true);
      setSwotError(null);

      const payload = {
        entity_id: entityId,
        company_name: entityName,
        financial_metrics: explanationData.financial_metrics || {
          debt_to_equity: explanationData.sensitivity_analysis?.debt_to_equity?.base_value || 0,
          current_ratio: explanationData.sensitivity_analysis?.current_ratio?.base_value || 0,
          debt_service_coverage_ratio: explanationData.sensitivity_analysis?.debt_service_coverage_ratio?.base_value || 0,
          net_profit_margin: 0,
          return_on_assets: 0
        },
        market_sentiment: explanationData.market_sentiment || {
          composite_sentiment_score: 0,
          market_tone: 'NEUTRAL'
        },
        industry_data: explanationData.industry_data || {
          industry: 'General',
          growth_rate_cagr: 0,
          market_attractiveness: 'MODERATE'
        }
      };

      const swot = await explainabilityService.generateSwotAnalysis(payload);
      setSwotData(swot);
    } catch (err) {
      setSwotError(err.message || 'Failed to generate SWOT analysis');
    } finally {
      setSwotLoading(false);
    }
  };

  const handleSensitivityAnalysis = async (metricName) => {
    try {
      // In production, call API
      const mockSensitivity = {
        metric_name: metricName,
        base_value: explanation.sensitivity_analysis[metricName].base_value,
        analysis: {
          '-30': 820,
          '-20': 805,
          '-10': 778,
          '0': 750,
          '10': 722,
          '20': 695,
          '30': 668
        }
      };
      setSensitivity(mockSensitivity);
    } catch (err) {
      setError('Failed to perform sensitivity analysis');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading explanation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-white p-8">
        <div className="text-center text-red-600">
          <p className="text-lg font-semibold mb-2">Error</p>
          <p>{error}</p>
          <button
            onClick={loadExplanation}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!explanation) {
    return <div className="flex items-center justify-center h-full bg-white">No explanation data</div>;
  }

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{entityName}</h2>
            <p className="text-gray-600 text-sm">Credit Decision Explanation & Analysis</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600">{explanation.final_score}</div>
              <div className="text-sm text-gray-600">Credit Score</div>
            </div>
            <div className="px-4 py-2 bg-blue-600 text-white rounded-lg text-center">
              <div className="text-xl font-bold">{explanation.final_rating}</div>
              <div className="text-xs">Rating</div>
            </div>
            <button
              onClick={onClose}
              className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              ✕
            </button>
          </div>
        </div>
      </div>

      {/* Decision Summary */}
      <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <p className="text-lg font-semibold text-blue-900">
              {explanation.decision === 'APPROVE' && '✓ Recommended for Approval'}
              {explanation.decision === 'CONDITIONAL_APPROVE' && '~ Conditional Approval Recommended'}
              {explanation.decision === 'DECLINE' && '✗ Decline Recommended'}
            </p>
            <p className="text-sm text-blue-700 mt-1">
              Confidence: {(explanation.decision_confidence * 100).toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Explanation Confidence</p>
            <p className="text-2xl font-bold text-blue-600">{(explanation.explanation_confidence * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="flex">
          {['overview', 'importance', 'risks', 'sensitivity', 'swot'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-medium capitalize border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'importance' && '📊 Feature Importance'}
              {tab === 'risks' && '⚠️ Risk Analysis'}
              {tab === 'sensitivity' && '📈 Sensitivity'}
              {tab === 'swot' && '🧠 SWOT Analysis'}
              {tab === 'overview' && '📋 Overview'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'overview' && (
          <OverviewTab explanation={explanation} />
        )}
        {activeTab === 'importance' && (
          <FeatureImportanceTab features={explanation.feature_importance} />
        )}
        {activeTab === 'risks' && (
          <RiskAnalysisTab
            riskFactors={explanation.top_risk_factors}
            strengths={explanation.strengths}
            concerns={explanation.concerns}
            recommendations={explanation.recommendations}
          />
        )}
        {activeTab === 'sensitivity' && (
          <SensitivityTab
            sensitivity={sensitivity}
            onAnalyze={handleSensitivityAnalysis}
            baseMetrics={explanation.sensitivity_analysis}
          />
        )}
        {activeTab === 'swot' && (
          <SwotTab
            swot={swotData}
            loading={swotLoading}
            error={swotError}
            onRefresh={() => loadSwotAnalysis(explanation)}
          />
        )}
      </div>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ explanation }) {
  return (
    <div className="p-6 space-y-6">
      {/* Executive Summary */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 className="font-semibold text-gray-900 mb-2">Executive Summary</h3>
        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
          {explanation.executive_summary}
        </p>
      </div>

      {/* Key Findings */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">Key Findings</h3>
        <ul className="space-y-2">
          {explanation.key_findings.map((finding, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700">
              <span className="text-blue-600 font-bold">•</span>
              <span>{finding}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Strengths & Concerns */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold text-green-700 mb-3">Strengths</h3>
          <ul className="space-y-2">
            {explanation.strengths.map((strength, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-green-600">✓</span>
                <span>{strength}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-red-700 mb-3">Concerns</h3>
          <ul className="space-y-2">
            {explanation.concerns.map((concern, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-700">
                <span className="text-red-600">!</span>
                <span>{concern}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
        <h3 className="font-semibold text-gray-900 mb-3">Recommendations</h3>
        <ol className="space-y-2">
          {explanation.recommendations.map((rec, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700">
              <span className="text-yellow-600 font-bold">{i + 1}.</span>
              <span>{rec}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Top Contributing Factors */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">Top Contributing Factors</h3>
        <ul className="space-y-2">
          {explanation.top_contributing_factors.map((factor, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700 p-2 bg-gray-50 rounded">
              <span className="text-blue-600 font-bold">#{i + 1}</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// Feature Importance Tab Component
function FeatureImportanceTab({ features }) {
  return (
    <div className="p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Feature Importance Ranking</h3>
      <div className="space-y-3">
        {features.map((feature, i) => (
          <div key={i} className="border border-gray-200 rounded-lg p-3">
            <div className="flex justify-between items-center mb-2">
              <div>
                <div className="font-semibold text-gray-900">{i + 1}. {feature.feature_name}</div>
                <div className="text-xs text-gray-600 mt-1">
                  <span className={`px-2 py-1 rounded text-white text-xs font-semibold mr-2 ${
                    feature.direction === 'POSITIVE' ? 'bg-green-600' : 
                    feature.direction === 'NEGATIVE' ? 'bg-red-600' : 
                    'bg-gray-600'
                  }`}>
                    {feature.direction}
                  </span>
                  <span className={`px-2 py-1 rounded text-white text-xs font-semibold ${
                    feature.impact_level === 'CRITICAL' ? 'bg-red-600' :
                    feature.impact_level === 'HIGH' ? 'bg-orange-600' :
                    feature.impact_level === 'MEDIUM' ? 'bg-yellow-600' :
                    'bg-blue-600'
                  }`}>
                    {feature.impact_level}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{feature.importance_score.toFixed(1)}</div>
                <div className="text-xs text-gray-600">importance</div>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${feature.importance_score}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-2">
              Contribution: {feature.contribution > 0 ? '+' : ''}{(feature.contribution * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Risk Analysis Tab Component
function RiskAnalysisTab({ riskFactors, strengths, concerns, recommendations }) {
  return (
    <div className="p-6 space-y-6">
      {/* Risk Factors */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-4">Risk Factors</h3>
        {riskFactors.length === 0 ? (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            ✓ No critical risk factors identified
          </div>
        ) : (
          <div className="space-y-3">
            {riskFactors.map((risk, i) => (
              <div key={i} className={`border-l-4 p-4 rounded ${
                risk.severity === 'CRITICAL' ? 'border-red-500 bg-red-50' :
                risk.severity === 'HIGH' ? 'border-orange-500 bg-orange-50' :
                risk.severity === 'MEDIUM' ? 'border-yellow-500 bg-yellow-50' :
                'border-blue-500 bg-blue-50'
              }`}>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-gray-900">{risk.factor_name}</h4>
                  <span className={`px-2 py-1 rounded text-white text-xs font-semibold ${
                    risk.severity === 'CRITICAL' ? 'bg-red-600' :
                    risk.severity === 'HIGH' ? 'bg-orange-600' :
                    risk.severity === 'MEDIUM' ? 'bg-yellow-600' :
                    'bg-blue-600'
                  }`}>
                    {risk.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{risk.description}</p>
                <div className="bg-white bg-opacity-50 p-2 rounded text-sm text-gray-700">
                  <strong>Recommendation:</strong> {risk.recommendation}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Strengths */}
      <div>
        <h3 className="font-semibold text-green-700 mb-3">Mitigating Factors</h3>
        <ul className="space-y-2">
          {strengths.map((strength, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-700 p-2 bg-green-50 rounded">
              <span className="text-green-600">✓</span>
              <span>{strength}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// Sensitivity Analysis Tab Component
function SensitivityTab({ sensitivity, onAnalyze, baseMetrics }) {
  return (
    <div className="p-6 space-y-6">
      <p className="text-gray-700 text-sm">
        Select a metric below to analyze how the credit score would change with different input values.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(baseMetrics).map(([metric, data]) => (
          <div key={metric} className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-3">{metric}</h4>
            <div className="text-sm text-gray-600 mb-3">
              <div>Base Value: {data.base_value.toFixed(2)}</div>
              <div>Elasticity: {data.elasticity}</div>
            </div>
            <button
              onClick={() => onAnalyze(metric)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
            >
              Analyze Impact
            </button>
          </div>
        ))}
      </div>

      {sensitivity && (
        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <h4 className="font-semibold text-gray-900 mb-4">
            Impact of {sensitivity.metric_name} Variations
          </h4>
          <div className="space-y-2">
            {Object.entries(sensitivity.analysis).map(([change, score]) => (
              <div key={change} className="flex justify-between items-center">
                <span className="text-sm text-gray-700">
                  {change === '0' ? 'Base' : `${change > 0 ? '+' : ''}${change}%`}
                </span>
                <div className="flex-1 mx-4 h-2 bg-gray-300 rounded">
                  <div
                    className="h-2 bg-blue-600 rounded"
                    style={{ width: `${(score / 850) * 100}%` }}
                  ></div>
                </div>
                <span className="font-semibold text-gray-900 min-w-12 text-right">{score}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SwotSectionCard({ title, emoji, items, tone }) {
  const toneClasses = {
    green: 'border-green-200 bg-green-50',
    red: 'border-red-200 bg-red-50',
    blue: 'border-blue-200 bg-blue-50',
    orange: 'border-orange-200 bg-orange-50'
  };

  return (
    <div className={`rounded-lg border ${toneClasses[tone] || 'border-gray-200 bg-gray-50'} overflow-hidden`}>
      <div className="px-4 py-3 border-b border-black border-opacity-5 flex items-center gap-2">
        <span>{emoji}</span>
        <h4 className="font-semibold text-gray-900">{title}</h4>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white bg-opacity-70">
              <th className="text-left px-3 py-2 w-12 text-gray-600 font-medium">#</th>
              <th className="text-left px-3 py-2 text-gray-600 font-medium">Insight</th>
            </tr>
          </thead>
          <tbody>
            {(items || []).map((item, idx) => (
              <tr key={idx} className="border-t border-black border-opacity-5">
                <td className="px-3 py-2 text-gray-500">{idx + 1}</td>
                <td className="px-3 py-2 text-gray-800">{item}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SwotTab({ swot, loading, error, onRefresh }) {
  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-3 text-gray-700">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span>Generating SWOT analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-red-700 text-sm mb-3">{error}</p>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
          >
            Retry SWOT
          </button>
        </div>
      </div>
    );
  }

  if (!swot) {
    return (
      <div className="p-6">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-700 text-sm">
          SWOT analysis is not available yet.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-start justify-between bg-gradient-to-r from-indigo-50 to-blue-50 border border-blue-100 rounded-lg p-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">SWOT Summary</h3>
          <p className="text-sm text-gray-700 mt-1">Structured LLM insights for underwriting review</p>
        </div>
        <div className="text-right text-xs text-gray-600">
          <div>Model: <span className="font-semibold text-gray-800">{swot.model_used}</span></div>
          <div className="mt-1">Generated: {new Date(swot.generated_at).toLocaleString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SwotSectionCard title="Strengths" emoji="💪" items={swot.strengths} tone="green" />
        <SwotSectionCard title="Weaknesses" emoji="🧩" items={swot.weaknesses} tone="red" />
        <SwotSectionCard title="Opportunities" emoji="🚀" items={swot.opportunities} tone="blue" />
        <SwotSectionCard title="Threats" emoji="⚠️" items={swot.threats} tone="orange" />
      </div>
    </div>
  );
}
