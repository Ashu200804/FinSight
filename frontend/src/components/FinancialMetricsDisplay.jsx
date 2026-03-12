import React, { useState, useEffect } from 'react';
import { metricsService } from '../services/metricsService';
import { extractionService } from '../services/extractionService';

export const FinancialMetricsDisplay = ({ documentId, entityId, onMetricsLoaded }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSection, setExpandedSection] = useState('profitability');
  const [metricsSource, setMetricsSource] = useState(null);

  useEffect(() => {
    if (documentId) {
      loadMetrics();
    }
  }, [documentId]);

  const loadMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      let targetDocumentId = documentId;
      let source = {
        type: 'latest',
        status: 'pending',
        documentId: documentId,
      };

      if (entityId) {
        try {
          const extractionRes = await extractionService.getResults(entityId);
          const reviewData = extractionRes?.data;
          const approvedDocId = reviewData?.status === 'approved' ? reviewData?.document_id : null;
          if (approvedDocId) {
            targetDocumentId = approvedDocId;
            source = {
              type: 'approved',
              status: reviewData?.status,
              documentId: approvedDocId,
            };
          }
        } catch (extractionErr) {
          source = {
            type: 'latest',
            status: 'pending',
            documentId: documentId,
          };
        }
      }

      const response = await metricsService.calculateMetrics(targetDocumentId);
      setMetrics(response);
      setMetricsSource(source);
      if (onMetricsLoaded) {
        onMetricsLoaded(response);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to calculate metrics');
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
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4v2m0 0v2m0-6V9m-6 4h12a2 2 0 012 2v7a2 2 0 01-2 2H6a2 2 0 01-2-2v-7a2 2 0 012-2z" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-600">No metrics calculated yet</p>
        <button
          onClick={loadMetrics}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Calculate Metrics
        </button>
      </div>
    );
  }

  const creditInputs = metrics.credit_score_inputs || {};
  const profitability = metrics.profitability_ratios || {};
  const liquidity = metrics.liquidity_ratios || {};
  const solvency = metrics.solvency_ratios || {};
  const efficiency = metrics.efficiency_ratios || {};

  return (
    <div className="space-y-6">
      {metricsSource?.type === 'approved' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm text-green-800">
            Showing metrics from approved extracted data (Document #{metricsSource.documentId}).
          </p>
        </div>
      )}

      {/* Overall Score Card */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg shadow-lg p-8">
        <h2 className="text-3xl font-bold mb-2">Financial Health Score</h2>
        <div className="grid grid-cols-5 gap-4 mt-6">
          <ScoreCard
            label="Overall"
            score={metricsService.calculateOverallScore({
              profitability: creditInputs.profitability_score?.score,
              liquidity: creditInputs.liquidity_score?.score,
              solvency: creditInputs.solvency_score?.score,
              efficiency: creditInputs.efficiency_score?.score,
            })}
            maxScore={100}
          />
          <ScoreCard
            label="Profitability"
            score={creditInputs.profitability_score?.score}
            maxScore={creditInputs.profitability_score?.max_score}
          />
          <ScoreCard
            label="Liquidity"
            score={creditInputs.liquidity_score?.score}
            maxScore={creditInputs.liquidity_score?.max_score}
          />
          <ScoreCard
            label="Solvency"
            score={creditInputs.solvency_score?.score}
            maxScore={creditInputs.solvency_score?.max_score}
          />
          <ScoreCard
            label="Efficiency"
            score={creditInputs.efficiency_score?.score}
            maxScore={creditInputs.efficiency_score?.max_score}
          />
        </div>
      </div>

      {/* Quick Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricQuick
          icon="📊"
          label="Leverage Status"
          value={creditInputs.leverage_assessment?.leverage_level?.replace(/_/g, ' ') || 'N/A'}
          riskLevel={creditInputs.leverage_assessment?.risk_level}
        />
        <MetricQuick
          icon="💰"
          label="Cash Flow"
          value={creditInputs.cash_flow_health?.status || 'N/A'}
          subtitle="Health Status"
        />
        <MetricQuick
          icon="📈"
          label="Current Ratio"
          value={liquidity.current_ratio?.value?.toFixed(2) || 'N/A'}
          benchmark={liquidity.current_ratio?.benchmark}
        />
        <MetricQuick
          icon="💵"
          label="Debt to Equity"
          value={solvency.debt_to_equity?.value?.toFixed(2) || 'N/A'}
          benchmark={solvency.debt_to_equity?.benchmark}
        />
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6 overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'profitability', label: 'Profitability' },
              { id: 'liquidity', label: 'Liquidity' },
              { id: 'solvency', label: 'Solvency' },
              { id: 'efficiency', label: 'Efficiency' },
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
              <RatioSection
                title="Key Financial Ratios"
                ratios={[
                  { name: 'Current Ratio', data: liquidity.current_ratio },
                  { name: 'Profit Margin', data: profitability.profit_margin },
                  { name: 'Debt to Equity', data: solvency.debt_to_equity },
                  { name: 'Return on Equity', data: profitability.return_on_equity },
                ]}
              />

              {/* Risk Assessment */}
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                <h4 className="font-semibold text-blue-900 mb-4">Risk Assessment</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-blue-700">Leverage Level</p>
                    <p className={`text-lg font-bold ${metricsService.getRiskLevelColor(creditInputs.leverage_assessment?.risk_level)}`}>
                      {creditInputs.leverage_assessment?.leverage_level?.replace(/_/g, ' ') || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-700">Risk Level</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${metricsService.getRiskLevelBadge(creditInputs.leverage_assessment?.risk_level)}`}>
                      {creditInputs.leverage_assessment?.risk_level?.toUpperCase() || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Profitability Tab */}
          {activeTab === 'profitability' && (
            <RatioSection
              title="Profitability Metrics"
              ratios={Object.entries(profitability).map(([key, value]) => ({
                name: key.replace(/_/g, ' ').toUpperCase(),
                data: value,
              }))}
              expandedSection={expandedSection}
              onToggleSection={setExpandedSection}
            />
          )}

          {/* Liquidity Tab */}
          {activeTab === 'liquidity' && (
            <RatioSection
              title="Liquidity Metrics"
              ratios={Object.entries(liquidity).map(([key, value]) => ({
                name: key.replace(/_/g, ' ').toUpperCase(),
                data: value,
              }))}
            />
          )}

          {/* Solvency Tab */}
          {activeTab === 'solvency' && (
            <RatioSection
              title="Solvency Metrics"
              ratios={Object.entries(solvency).map(([key, value]) => ({
                name: key.replace(/_/g, ' ').toUpperCase(),
                data: value,
              }))}
            />
          )}

          {/* Efficiency Tab */}
          {activeTab === 'efficiency' && (
            <RatioSection
              title="Efficiency Metrics"
              ratios={Object.entries(efficiency).map(([key, value]) => ({
                name: key.replace(/_/g, ' ').toUpperCase(),
                data: value,
              }))}
            />
          )}
        </div>
      </div>

      {/* Warnings and Errors */}
      {(metrics.warnings?.length > 0 || metrics.errors?.length > 0) && (
        <div className="space-y-4">
          {metrics.warnings?.map((warning, idx) => (
            <div key={`w-${idx}`} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">⚠️ {warning}</p>
            </div>
          ))}
          {metrics.errors?.map((error, idx) => (
            <div key={`e-${idx}`} className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">❌ {error}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Helper Components
const ScoreCard = ({ label, score, maxScore = 100 }) => {
  const percentage = (score / maxScore) * 100;
  return (
    <div className="text-center">
      <div className="relative inline-flex items-center justify-center w-20 h-20 mb-2">
        <div className="absolute w-full h-full rounded-full border-4 border-white border-opacity-30"></div>
        <span className="text-2xl font-bold">{score?.toFixed(0) || 0}</span>
      </div>
      <p className="text-xs font-semibold opacity-90">{label}</p>
    </div>
  );
};

const MetricQuick = ({ icon, label, value, benchmark, riskLevel, subtitle }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-gray-600 text-sm font-medium">{label}</p>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className={`text-2xl font-bold ${riskLevel ? metricsService.getRiskLevelColor(riskLevel) : 'text-gray-900'}`}>
        {value}
      </p>
      {benchmark && <p className="text-xs text-gray-500 mt-1">Benchmark: {benchmark}</p>}
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
};

const RatioSection = ({ title, ratios, expandedSection, onToggleSection }) => {
  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-gray-900 text-lg">{title}</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ratios.map((ratio, idx) => {
          const data = ratio.data || {};
          const isExpanded = expandedSection === ratio.name;

          if (data.status === 'error') {
            return (
              <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="font-medium text-gray-900">{ratio.name}</p>
                <p className="text-sm text-gray-500 mt-2">{data.reason || 'Data not available'}</p>
              </div>
            );
          }

          return (
            <div
              key={idx}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
              onClick={() => onToggleSection && onToggleSection(isExpanded ? null : ratio.name)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-gray-900">{ratio.name}</p>
                  <p className="text-2xl font-bold text-blue-600 mt-2">
                    {metricsService.formatRatio(data.value, data.unit)}
                  </p>
                </div>
                {data.value && (
                  <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                    ✓
                  </span>
                )}
              </div>

              {isExpanded && data.interpretation && (
                <div className="mt-4 pt-4 border-t border-gray-300">
                  <p className="text-sm text-gray-700">{data.interpretation}</p>
                  {data.benchmark && <p className="text-xs text-gray-500 mt-2">📊 {data.benchmark}</p>}
                  {data.warning && <p className="text-xs text-yellow-700 mt-2">{data.warning}</p>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FinancialMetricsDisplay;
