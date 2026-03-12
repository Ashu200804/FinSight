import React, { useEffect, useState } from 'react';
import { camService } from '@/services/camService';

export function CAMHistoryDashboard({ entityId, entityName }) {
  const [history, setHistory] = useState([]);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  const loadCamWorkspace = async () => {
    try {
      setLoading(true);
      setError(null);
      const [historyData, previewData] = await Promise.all([
        camService.getCamHistory(entityId),
        camService.getCamPreview(entityId),
      ]);
      setHistory(historyData.reports || []);
      setPreview(previewData || null);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load CAM workspace');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (entityId) {
      loadCamWorkspace();
    }
  }, [entityId]);

  const handleGenerateCam = async () => {
    try {
      setGenerating(true);
      setError(null);
      await camService.generateCam(entityId);
      await loadCamWorkspace();
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate CAM');
    } finally {
      setGenerating(false);
    }
  };

  const formatApproval = (p) => {
    if (p === null || p === undefined) return 'N/A';
    return `${(Number(p) * 100).toFixed(1)}%`;
  };

  const approvalClass = (p) => {
    if (p === null || p === undefined) return 'bg-gray-100 text-gray-700';
    if (p >= 0.8) return 'bg-green-100 text-green-800';
    if (p >= 0.6) return 'bg-blue-100 text-blue-800';
    if (p >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatScore = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return Number(value).toFixed(1);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${Number(value).toFixed(2)}%`;
  };

  const getBarColor = (value) => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 60) return 'bg-blue-500';
    if (value >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const scoreBars = [
    { key: 'overall_health_score', label: 'Overall Health' },
    { key: 'profitability_score', label: 'Profitability' },
    { key: 'liquidity_score', label: 'Liquidity' },
    { key: 'solvency_score', label: 'Solvency' },
    { key: 'efficiency_score', label: 'Efficiency' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden space-y-0">
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-slate-50 to-blue-50 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">CAM Generation Workspace</h3>
          <p className="text-sm text-gray-600">{entityName || `Entity ${entityId}`}</p>
        </div>
        <button
          onClick={handleGenerateCam}
          disabled={generating}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400"
        >
          {generating ? 'Generating Final CAM PDF...' : 'Generate Final CAM PDF'}
        </button>
      </div>

      {error && (
        <div className="mx-6 mt-4 p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="p-6">
        {loading ? (
          <div className="text-sm text-gray-600">Loading CAM workspace...</div>
        ) : (
          <div className="space-y-6">
            {preview && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                  <MetricCard label="Credit Score" value={preview.scorecard?.credit_score ?? 'N/A'} />
                  <MetricCard label="Risk Category" value={preview.scorecard?.risk_category || 'N/A'} />
                  <MetricCard label="Probability of Default" value={formatPercent(preview.scorecard?.probability_of_default)} />
                  <MetricCard label="Recommended Decision" value={preview.recommendation?.decision || 'N/A'} />
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-4">Financial Score Visuals</h4>
                    <div className="space-y-3">
                      {scoreBars.map(({ key, label }) => {
                        const value = Number(preview.financial_analysis?.[key] || 0);
                        const width = Math.max(0, Math.min(100, value));
                        return (
                          <div key={key}>
                            <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
                              <span>{label}</span>
                              <span className="font-semibold">{formatScore(value)}</span>
                            </div>
                            <div className="h-2 rounded bg-gray-100 overflow-hidden">
                              <div className={`h-2 ${getBarColor(value)}`} style={{ width: `${width}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-4">Core Financial Metrics</h4>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <MetricRow label="Debt/Equity" value={formatScore(preview.financial_analysis?.debt_to_equity)} />
                      <MetricRow label="Current Ratio" value={formatScore(preview.financial_analysis?.current_ratio)} />
                      <MetricRow label="DSCR" value={formatScore(preview.financial_analysis?.debt_service_coverage_ratio)} />
                      <MetricRow label="Net Margin" value={formatPercent((preview.financial_analysis?.net_profit_margin || 0) * 100)} />
                      <MetricRow label="ROA" value={formatPercent((preview.financial_analysis?.return_on_assets || 0) * 100)} />
                      <MetricRow label="Market Tone" value={preview.market_snapshot?.tone || 'N/A'} />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  <ListPanel title="Top Feature Importance" items={preview.top_feature_importance} />
                  <ListPanel title="Top Risk Factors" items={preview.top_risk_factors} />
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  <ListPanel title="SWOT - Strengths" items={preview.swot?.strengths} />
                  <ListPanel title="SWOT - Weaknesses" items={preview.swot?.weaknesses} />
                  <ListPanel title="SWOT - Opportunities" items={preview.swot?.opportunities} />
                  <ListPanel title="SWOT - Threats" items={preview.swot?.threats} />
                </div>

                <div className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">Final CAM Recommendation</h4>
                  <div className="text-sm text-blue-900 space-y-1">
                    <p><span className="font-semibold">Decision:</span> {preview.recommendation?.decision || 'N/A'}</p>
                    <p><span className="font-semibold">Requested Amount:</span> {preview.recommendation?.requested_amount || 'N/A'}</p>
                    <p><span className="font-semibold">Rate Guidance:</span> {preview.recommendation?.suggested_rate_guidance || 'N/A'}</p>
                    <p><span className="font-semibold">Conditions:</span> {preview.recommendation?.key_conditions || 'N/A'}</p>
                    <p><span className="font-semibold">Rationale:</span> {preview.recommendation?.rationale || 'N/A'}</p>
                  </div>
                </div>
              </>
            )}

            {history.length === 0 ? (
              <div className="text-sm text-gray-600">No CAM reports generated yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-sm border border-gray-200 rounded-lg overflow-hidden">
                  <thead className="bg-gray-50 text-gray-700">
                    <tr>
                      <th className="text-left px-4 py-3 font-semibold">Report ID</th>
                      <th className="text-left px-4 py-3 font-semibold">Created At</th>
                      <th className="text-left px-4 py-3 font-semibold">Credit Score</th>
                      <th className="text-left px-4 py-3 font-semibold">Risk Category</th>
                      <th className="text-left px-4 py-3 font-semibold">Approval Probability</th>
                      <th className="text-left px-4 py-3 font-semibold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((report) => (
                      <tr key={report.id} className="border-t border-gray-200 hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-900">#{report.id}</td>
                        <td className="px-4 py-3 text-gray-700">{new Date(report.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3 text-gray-700">{report.credit_score ?? 'N/A'}</td>
                        <td className="px-4 py-3 text-gray-700">{report.risk_category || 'N/A'}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${approvalClass(report.approval_probability)}`}>
                            {formatApproval(report.approval_probability)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => camService.downloadStoredCam(report.id)}
                            className="px-3 py-1.5 text-xs font-medium rounded-md bg-slate-900 text-white hover:bg-slate-700"
                          >
                            Download PDF
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
      <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

function MetricRow({ label, value }) {
  return (
    <div className="p-3 rounded border border-gray-200 bg-white">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-base font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function ListPanel({ title, items }) {
  return (
    <div className="p-4 border border-gray-200 rounded-lg">
      <h4 className="font-semibold text-gray-900 mb-3">{title}</h4>
      {!items || items.length === 0 ? (
        <p className="text-sm text-gray-500">Not available</p>
      ) : (
        <ul className="space-y-2 text-sm text-gray-700 list-disc pl-5">
          {items.slice(0, 5).map((item, idx) => (
            <li key={`${title}-${idx}`}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CAMHistoryDashboard;
