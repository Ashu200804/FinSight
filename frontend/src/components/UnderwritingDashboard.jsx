import React, { useState, useEffect } from 'react';
import { creditScoringService } from '../services/creditScoringService';
import CreditScoringDisplay from './CreditScoringDisplay';

export const UnderwritingDashboard = ({ entityId, entityName, onNavigate }) => {
  const [activeView, setActiveView] = useState('scoring');
  const [scoringHistory, setScoringHistory] = useState([]);
  const [scoringMethodology, setScoringMethodology] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (entityId) {
      loadScoringHistory();
      loadMethodology();
    }
  }, [entityId]);

  const loadScoringHistory = async () => {
    setHistoryLoading(true);
    try {
      const historyResponse = await creditScoringService.getCreditScoreHistory(entityId, 12);

      const riskToGrade = (risk) => {
        const mapping = {
          EXCELLENT: 'AAA',
          VERY_GOOD: 'AA',
          GOOD: 'A',
          FAIR: 'BBB',
          POOR: 'BB',
          VERY_POOR: 'B',
          UNACCEPTABLE: 'CCC',
        };
        return mapping[risk] || 'N/A';
      };

      const normalized = Array.isArray(historyResponse)
        ? historyResponse
        : (historyResponse?.scores || []).map((row, idx) => ({
            id: `${row.date || row.created_at || idx}`,
            created_at: row.date || row.created_at,
            credit_score: row.credit_score,
            grade: riskToGrade(row.risk_category),
            probability_of_default: row.probability_of_default || 0,
            change_reason: row.score_change ? `Score change: ${row.score_change}` : null,
            risk_category: row.risk_category,
          }));

      setScoringHistory(normalized);
    } catch (err) {
      setError('Failed to load scoring history');
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadMethodology = async () => {
    try {
      const methodology = await creditScoringService.getScoringMethodology();
      setScoringMethodology(methodology);
    } catch (err) {
      // Methodology may not be available
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6 rounded-t-lg">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{entityName}</h1>
            <p className="text-sm text-gray-600 mt-1">Credit Underwriting Assessment</p>
          </div>
          <div className="flex gap-2">
            {[
              { id: 'scoring', label: 'Credit Score', icon: '📊' },
              { id: 'history', label: 'Score History', icon: '📈' },
              { id: 'methodology', label: 'Methodology', icon: '📋' },
              { id: 'recommendations', label: 'Recommendations', icon: '💡' },
            ].map((view) => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  activeView === view.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {view.icon} {view.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {activeView === 'scoring' && (
          <CreditScoringDisplay
            entityId={entityId}
            entityName={entityName}
            onScoringComplete={() => loadScoringHistory()}
          />
        )}

        {activeView === 'history' && (
          <ScoringHistoryView
            history={scoringHistory}
            loading={historyLoading}
            onRefresh={loadScoringHistory}
          />
        )}

        {activeView === 'methodology' && (
          <MethodologyView methodology={scoringMethodology} />
        )}

        {activeView === 'recommendations' && (
          <RecommendationsView entityId={entityId} />
        )}
      </div>
    </div>
  );
};

// Scoring History View
const ScoringHistoryView = ({ history, loading, onRefresh }) => {
  const [selectedScore, setSelectedScore] = useState(null);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className="bg-white rounded-lg p-8 text-center">
        <p className="text-gray-600">No scoring history available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Trend Chart */}
      <div className="bg-white rounded-lg p-6 shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trend</h3>
        <ScoreTrendChart scores={history} />
      </div>

      {/* History Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Score History</h3>
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Grade
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  PD
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Change
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Reason
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {history.map((record, idx) => {
                const previousScore = history[idx + 1]?.credit_score;
                const change = previousScore ? record.credit_score - previousScore : 0;

                return (
                  <tr
                    key={record.id}
                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => setSelectedScore(record)}
                  >
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(record.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      {record.credit_score}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        getGradeBadge(record.grade)
                      }`}>
                        {record.grade}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {record.probability_of_default.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {change !== 0 ? (
                        <span className={`font-semibold ${
                          change > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {change > 0 ? '+' : ''}{change}
                        </span>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {record.change_reason || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Score Details Modal */}
      {selectedScore && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-gray-200 sticky top-0 bg-white">
              <h3 className="text-lg font-semibold text-gray-900">
                Score Details - {new Date(selectedScore.created_at).toLocaleDateString()}
              </h3>
              <button
                onClick={() => setSelectedScore(null)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 font-medium">Credit Score</p>
                  <p className="text-3xl font-bold text-blue-600 mt-1">{selectedScore.credit_score}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 font-medium">Grade</p>
                  <p className="text-3xl font-bold text-purple-600 mt-1">{selectedScore.grade}</p>
                </div>
                <div className="bg-orange-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 font-medium">Default Probability</p>
                  <p className="text-3xl font-bold text-orange-600 mt-1">
                    {selectedScore.probability_of_default.toFixed(2)}%
                  </p>
                </div>
              </div>

              {selectedScore.change_reason && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-semibold text-gray-900 mb-2">Change Reason</p>
                  <p className="text-sm text-gray-700">{selectedScore.change_reason}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Scoring Methodology View
const MethodologyView = ({ methodology }) => {
  const scorers = [
    {
      id: 'financial_strength',
      name: 'Financial Strength',
      weight: '20%',
      description: 'Evaluates profitability, liquidity, and asset efficiency',
      factors: ['Profit Margin', 'ROA', 'ROE', 'EBITDA Margin', 'Current Ratio'],
    },
    {
      id: 'bank_relationship',
      name: 'Bank Relationship',
      weight: '15%',
      description: 'Assesses tenure and repayment history with lending institution',
      factors: ['Years with Bank', 'Facility Types', 'Repayment History', 'Complaints'],
    },
    {
      id: 'industry_risk',
      name: 'Industry Risk',
      weight: '15%',
      description: 'Evaluates sector growth and regulatory environment',
      factors: ['Sector Growth Rate', 'Regulatory Environment', 'Industry Stability'],
    },
    {
      id: 'management_quality',
      name: 'Management Quality',
      weight: '10%',
      description: 'Assesses management experience and track record',
      factors: ['Experience Years', 'Education Level', 'Track Record'],
    },
    {
      id: 'collateral_strength',
      name: 'Collateral Strength',
      weight: '10%',
      description: 'Evaluates collateral value and quality',
      factors: ['Collateral Type', 'Collateral Value', 'LTV Ratio', 'Lien Status'],
    },
    {
      id: 'legal_risk',
      name: 'Legal Risk',
      weight: '10%',
      description: 'Assesses litigation and regulatory compliance',
      factors: ['Litigation Count', 'Violations', 'Pending Cases'],
    },
    {
      id: 'fraud_risk',
      name: 'Fraud Risk',
      weight: '10%',
      description: 'Evaluates fraud history and AML compliance',
      factors: ['Fraud Flags', 'Chargeback History', 'AML Risk Level'],
    },
    {
      id: 'credit_bureau',
      name: 'Credit Bureau Score',
      weight: '10%',
      description: 'Evaluates credit bureau reports and default history',
      factors: ['CIBIL Score', 'Bureau Enquiries', 'Default History'],
    },
  ];

  const gradeScale = [
    { grade: 'AAA', score: '80-100', risk: 'Minimal', color: 'bg-green-100' },
    { grade: 'AA', score: '70-79', risk: 'Very Low', color: 'bg-green-50' },
    { grade: 'A', score: '60-69', risk: 'Low', color: 'bg-blue-100' },
    { grade: 'BBB', score: '50-59', risk: 'Moderate', color: 'bg-yellow-100' },
    { grade: 'BB', score: '40-49', risk: 'High', color: 'bg-orange-100' },
    { grade: 'B', score: '30-39', risk: 'Very High', color: 'bg-red-100' },
    { grade: 'CCC', score: '20-29', risk: 'Severe', color: 'bg-red-200' },
    { grade: 'D', score: '0-19', risk: 'Default', color: 'bg-red-300' },
  ];

  return (
    <div className="space-y-8">
      {/* Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Scoring Overview</h3>
        <p className="text-gray-700 leading-relaxed">
          The credit scoring engine uses an 8-component weighted model to assess credit risk. Each component
          evaluates a specific dimension of creditworthiness, from financial health to operational risk. The
          final score (0-100) is converted to a Probability of Default using a logistic function, providing a
          statistically calibrated measure of default risk.
        </p>
      </div>

      {/* Component Weights */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Component Weights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scorers.map((scorer) => (
            <div key={scorer.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-semibold text-gray-900">{scorer.name}</h4>
                <span className="text-lg font-bold text-blue-600">{scorer.weight}</span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{scorer.description}</p>
              <div className="flex flex-wrap gap-1">
                {scorer.factors.map((factor) => (
                  <span key={factor} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grade Scale */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Rating Scale</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {gradeScale.map((item) => (
            <div key={item.grade} className={`rounded-lg p-4 ${item.color}`}>
              <p className="text-2xl font-bold text-gray-900">{item.grade}</p>
              <p className="text-sm text-gray-600 mt-1">Score: {item.score}</p>
              <p className="text-sm font-medium text-gray-700 mt-1">Risk: {item.risk}</p>
            </div>
          ))}
        </div>
      </div>

      {/* POD Calculation */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Probability of Default</h3>
        <p className="text-gray-700 mb-4">
          POD is calculated using a logistic transformation of the weighted credit score:
        </p>
        <div className="bg-white rounded-lg p-4 font-mono text-sm overflow-x-auto mb-4">
          <code className="text-blue-600">POD = 100 / (1 + e^(score/25))</code>
        </div>
        <p className="text-sm text-gray-600">
          This formula creates an S-curve where scores near 100 produce minimal default probability (~1%),
          while scores near 0 indicate high default probability (~99%). A score of 50 corresponds to 50% POD.
        </p>
      </div>
    </div>
  );
};

// Recommendations View
const RecommendationsView = ({ entityId }) => {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRecommendations();
  }, [entityId]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const data = await creditScoringService.getRecommendations(entityId);
      setRecommendations(data);
    } catch (err) {
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">{error}</div>;
  }

  if (!recommendations) {
    return <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-600">No recommendations available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Primary Recommendation */}
      <div className={`rounded-lg shadow p-6 border-l-4 ${
        recommendations.action === 'APPROVE' ? 'bg-green-50 border-green-500' :
        recommendations.action === 'DECLINE' ? 'bg-red-50 border-red-500' :
        'bg-yellow-50 border-yellow-500'
      }`}>
        <h3 className={`text-lg font-semibold ${
          recommendations.action === 'APPROVE' ? 'text-green-900' :
          recommendations.action === 'DECLINE' ? 'text-red-900' :
          'text-yellow-900'
        }`}>
          {recommendations.action === 'APPROVE' ? '✓ Approval Recommended' :
           recommendations.action === 'DECLINE' ? '✗ Decline Recommended' :
           '⏳ Conditional Approval'}
        </h3>
        <p className={`text-sm mt-2 ${
          recommendations.action === 'APPROVE' ? 'text-green-700' :
          recommendations.action === 'DECLINE' ? 'text-red-700' :
          'text-yellow-700'
        }`}>
          {recommendations.rationale}
        </p>
      </div>

      {/* Recommended Terms */}
      {recommendations.recommended_terms && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Terms</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.recommended_terms.map((term, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-900">{term.parameter}</p>
                <p className="text-lg font-bold text-blue-600 mt-2">{term.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conditions */}
      {recommendations.conditions && recommendations.conditions.length > 0 && (
        <div className="bg-blue-50 rounded-lg shadow p-6 border border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Required Conditions</h3>
          <ul className="space-y-2">
            {recommendations.conditions.map((condition, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                <span className="text-blue-600 font-bold mt-0.5">•</span>
                <span>{condition}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk Mitigants */}
      {recommendations.risk_mitigants && recommendations.risk_mitigants.length > 0 && (
        <div className="bg-green-50 rounded-lg shadow p-6 border border-green-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Mitigants</h3>
          <ul className="space-y-2">
            {recommendations.risk_mitigants.map((mitigant, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                <span className="text-green-600 font-bold mt-0.5">✓</span>
                <span>{mitigant}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk Factors */}
      {recommendations.risk_factors && recommendations.risk_factors.length > 0 && (
        <div className="bg-red-50 rounded-lg shadow p-6 border border-red-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Primary Risk Factors</h3>
          <ul className="space-y-2">
            {recommendations.risk_factors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                <span className="text-red-600 font-bold mt-0.5">⚠</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Monitoring params */}
      {recommendations.monitoring_parameters && recommendations.monitoring_parameters.length > 0 && (
        <div className="bg-purple-50 rounded-lg shadow p-6 border border-purple-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monitoring Parameters</h3>
          <ul className="space-y-2">
            {recommendations.monitoring_parameters.map((param, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-700">
                <span className="text-purple-600 font-bold mt-0.5">→</span>
                <span>{param}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Steps */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Next Steps</h3>
        <ol className="space-y-2 list-decimal list-inside text-sm text-gray-700">
          <li>Review full credit score breakdown and component scores</li>
          <li>Validate data completeness and accuracy</li>
          <li>Discuss recommended terms with credit committee</li>
          <li>If approved, establish monitoring framework</li>
          <li>Conduct final approval and document underwriting decision</li>
        </ol>
      </div>
    </div>
  );
};

// Helper Components
const ScoreTrendChart = ({ scores }) => {
  if (!scores || scores.length < 2) {
    return <p className="text-gray-600 text-center py-8">Insufficient data for trend analysis</p>;
  }

  const maxScore = Math.max(...scores.map(s => s.credit_score));
  const minScore = Math.min(...scores.map(s => s.credit_score));
  const range = maxScore - minScore || 10;
  const orderedScores = [...scores].reverse();

  return (
    <div className="flex items-end h-64 space-x-2">
      {orderedScores.map((score, idx) => {
        const height = ((score.credit_score - minScore) / range) * 100;
        const date = new Date(score.created_at);

        return (
          <div key={score.id} className="flex-1 flex flex-col items-center">
            <div className="relative w-full">
              <div
                className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-lg transition-all hover:from-blue-600 hover:to-blue-500 cursor-pointer group"
                style={{ height: `${Math.max(height, 5)}%` }}
              >
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                  {score.credit_score}
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-top-left whitespace-nowrap">
              {date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </p>
          </div>
        );
      })}
    </div>
  );
};

const getGradeBadge = (grade) => {
  const badges = {
    'AAA': 'bg-green-100 text-green-800',
    'AA': 'bg-green-100 text-green-800',
    'A': 'bg-blue-100 text-blue-800',
    'BBB': 'bg-yellow-100 text-yellow-800',
    'BB': 'bg-orange-100 text-orange-800',
    'B': 'bg-red-100 text-red-800',
    'CCC': 'bg-red-200 text-red-900',
    'D': 'bg-red-300 text-red-900',
  };
  return badges[grade] || 'bg-gray-100 text-gray-800';
};

export default UnderwritingDashboard;
