import React, { useState, useEffect } from 'react';
import { researchService } from '../services/researchService';

/**
 * Research Dashboard Component
 * 
 * Comprehensive research interface aggregating news, legal,
 * sentiment, and industry intelligence
 */
export const ResearchDashboard = ({ entityId, entityName, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    loadLatestReport();
  }, [entityId]);

  const loadLatestReport = async () => {
    setLoading(true);
    try {
      const data = await researchService.getEntityLatestReport(entityId);
      setReport(normalizeReportForOverview(data));
    } catch (err) {
      // Report may not exist yet
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const generateComprehensiveReport = async () => {
    setGeneratingReport(true);
    setError(null);
    try {
      const data = await researchService.generateComprehensiveResearch({
        entity_id: entityId,
        company_name: entityName,
        include_news: true,
        include_legal: true,
        include_sentiment: true,
        include_industry: true
      });
      setReport(normalizeReportForOverview(data));
    } catch (err) {
      setError('Failed to generate research report');
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white p-6 rounded-t-lg">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold">{entityName}</h2>
            <p className="text-indigo-100 mt-1">Company Research & Intelligence</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex space-x-1 px-6 overflow-x-auto">
          {[
            { id: 'overview', label: '📊 Overview' },
            { id: 'news', label: '📰 News' },
            { id: 'legal', label: '⚖️ Legal' },
            { id: 'sentiment', label: '💭 Sentiment' },
            { id: 'industry', label: '🏭 Industry' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <OverviewTab report={report} onGenerate={generateComprehensiveReport} generating={generatingReport} />
        )}

        {/* News Tab */}
        {activeTab === 'news' && <NewsTab entityId={entityId} />}

        {/* Legal Tab */}
        {activeTab === 'legal' && <LegalTab entityId={entityId} />}

        {/* Sentiment Tab */}
        {activeTab === 'sentiment' && <SentimentTab entityId={entityId} />}

        {/* Industry Tab */}
        {activeTab === 'industry' && <IndustryTab entityId={entityId} />}
      </div>
    </div>
  );
};

const normalizeReportForOverview = (rawReport) => {
  if (!rawReport) return null;

  if (rawReport.sections && rawReport.overall_assessment) {
    return rawReport;
  }

  const keyFindings = rawReport.key_findings || [];
  const strengths = rawReport.strengths || [];
  const weaknesses = rawReport.weaknesses || [];
  const risks = rawReport.risks || [];
  const recommendations = rawReport.recommendations || [];

  return {
    ...rawReport,
    generated_at: rawReport.generated_at || rawReport.created_at,
    sections: {
      executive_summary: {
        key_findings: keyFindings,
      },
    },
    overall_assessment: {
      overall_rating: rawReport.overall_rating,
      reliability_score: rawReport.reliability_score,
      key_strengths: strengths,
      key_weaknesses: weaknesses,
      critical_issues: risks,
      recommendations,
    },
  };
};

// Overview Tab Component
const OverviewTab = ({ report, onGenerate, generating }) => {
  if (!report) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-6">No research report available yet</p>
        <button
          onClick={onGenerate}
          disabled={generating}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 font-medium"
        >
          {generating ? '⏳ Generating Report...' : '🔍 Generate Comprehensive Research'}
        </button>
      </div>
    );
  }

  const executive = report.sections?.executive_summary || {};
  const assessment = report.overall_assessment || {};
  const reliabilityScore = Number(assessment.reliability_score || 0);

  return (
    <div className="space-y-6">
      {/* Report Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Overall Rating</p>
          <p className="text-2xl font-bold text-blue-600 mt-2">{assessment.overall_rating}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Reliability Score</p>
          <p className="text-2xl font-bold text-green-600 mt-2">
            {(reliabilityScore * 100).toFixed(0)}%
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Data Sources</p>
          <p className="text-2xl font-bold text-purple-600 mt-2">
            {Object.keys(report.sections || {}).length}
          </p>
        </div>
        <div className="bg-amber-50 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Report Date</p>
          <p className="text-sm text-amber-600 mt-2">
            {report.generated_at ? new Date(report.generated_at).toLocaleDateString() : '-'}
          </p>
        </div>
      </div>

      {/* Key Findings */}
      {executive.key_findings && (
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Findings</h3>
          <ul className="space-y-2">
            {executive.key_findings.map((finding, idx) => (
              <li key={idx} className="flex items-start gap-3 text-gray-700">
                <span className="text-blue-600 font-bold mt-0.5">•</span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {assessment.key_strengths && (
          <div className="bg-green-50 rounded-lg p-6 border border-green-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">✓ Strengths</h3>
            <ul className="space-y-2">
              {assessment.key_strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700">
                  <span className="text-green-600 font-bold">+</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {assessment.key_weaknesses && assessment.key_weaknesses.length > 0 && (
          <div className="bg-red-50 rounded-lg p-6 border border-red-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">⚠ Weaknesses</h3>
            <ul className="space-y-2">
              {assessment.key_weaknesses.map((weakness, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700">
                  <span className="text-red-600 font-bold">−</span>
                  <span>{weakness}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Critical Issues */}
      {assessment.critical_issues && assessment.critical_issues.length > 0 && (
        <div className="bg-red-50 rounded-lg p-6 border border-red-500">
          <h3 className="text-lg font-semibold text-red-900 mb-4">🚨 Critical Issues</h3>
          <ul className="space-y-2">
            {assessment.critical_issues.map((issue, idx) => (
              <li key={idx} className="text-red-700">{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {assessment.recommendations && (
        <div className="bg-indigo-50 rounded-lg p-6 border border-indigo-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Recommendations</h3>
          <ol className="space-y-2 list-decimal list-inside">
            {assessment.recommendations.map((rec, idx) => (
              <li key={idx} className="text-gray-700">{rec}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

// News Tab Component
const NewsTab = ({ entityId }) => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(null);

  useEffect(() => {
    loadNews();
  }, [entityId]);

  const loadNews = async () => {
    setLoading(true);
    try {
      const data = await researchService.getEntityNews(entityId);
      setNews(data);
    } catch (err) {
      console.error('Failed to load news');
    } finally {
      setLoading(false);
    }
  };

  const filteredNews = filter ? news.filter(n => n.sentiment === filter) : news;

  return (
    <div className="space-y-4">
      <div className="flex gap-2 mb-4">
        {['POSITIVE', 'NEUTRAL', 'NEGATIVE'].map((sentiment) => (
          <button
            key={sentiment}
            onClick={() => setFilter(filter === sentiment ? null : sentiment)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === sentiment
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {sentiment}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : filteredNews.length === 0 ? (
        <p className="text-gray-600 text-center py-8">No news articles found</p>
      ) : (
        <div className="space-y-3">
          {filteredNews.map((article) => (
            <NewsCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
};

const NewsCard = ({ article }) => {
  const sentimentColor = {
    POSITIVE: 'bg-green-100 text-green-800',
    NEGATIVE: 'bg-red-100 text-red-800',
    NEUTRAL: 'bg-gray-100 text-gray-800'
  }[article.sentiment] || 'bg-gray-100';

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 border border-gray-200 rounded-lg hover:shadow-lg hover:border-indigo-300 transition-all"
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 hover:text-indigo-600 line-clamp-2">
            {article.title}
          </h4>
          <p className="text-sm text-gray-600 mt-2">
            {article.source} • {new Date(article.published_at).toLocaleDateString()}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${sentimentColor}`}>
          {article.sentiment}
        </span>
      </div>
    </a>
  );
};

// Legal Tab Component
const LegalTab = ({ entityId }) => {
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLegalRisks();
  }, [entityId]);

  const loadLegalRisks = async () => {
    setLoading(true);
    try {
      const data = await researchService.getEntityLegalRisks(entityId);
      setRisks(data);
    } catch (err) {
      console.error('Failed to load legal risks');
    } finally {
      setLoading(false);
    }
  };

  const criticalRisks = risks.filter(r => r.severity === 'CRITICAL' || r.severity === 'HIGH');

  return (
    <div className="space-y-4">
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <>
          {criticalRisks.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-900 font-semibold">⚠️ {criticalRisks.length} Critical Risk(s) Identified</p>
            </div>
          )}
          
          {risks.length === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <p className="text-green-900 font-semibold">✓ No Legal Risks Detected</p>
            </div>
          ) : (
            <div className="space-y-3">
              {risks.map((risk) => (
                <RiskCard key={risk.id} risk={risk} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

const RiskCard = ({ risk }) => {
  const severityColor = {
    CRITICAL: 'bg-red-100 text-red-800 border-red-300',
    HIGH: 'bg-orange-100 text-orange-800 border-orange-300',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    LOW: 'bg-blue-100 text-blue-800 border-blue-300',
    NONE: 'bg-green-100 text-green-800 border-green-300'
  }[risk.severity] || 'bg-gray-100';

  return (
    <div className={`border-l-4 p-4 rounded-lg ${severityColor}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold text-gray-900">{risk.risk_type}</p>
          {risk.description && (
            <p className="text-sm text-gray-700 mt-1">{risk.description}</p>
          )}
          <p className="text-xs text-gray-600 mt-2">
            Status: <span className="font-semibold">{risk.status}</span> • 
            Detected: {new Date(risk.detection_date).toLocaleDateString()}
          </p>
        </div>
        {risk.count > 0 && (
          <span className="px-3 py-1 bg-white rounded-full text-sm font-bold">
            {risk.count} incident{risk.count !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  );
};

// Sentiment Tab Component
const SentimentTab = ({ entityId }) => {
  const [sentiment, setSentiment] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSentiment();
  }, [entityId]);

  const loadSentiment = async () => {
    setLoading(true);
    try {
      const data = await researchService.getEntitySentiment(entityId);
      setSentiment(data);
    } catch (err) {
      console.error('Failed to load sentiment');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!sentiment) {
    return <p className="text-gray-600 text-center py-8">No sentiment data available</p>;
  }

  return (
    <div className="space-y-6">
      {/* Composite Score */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6 border border-indigo-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Perception</h3>
        <div className="flex items-center space-x-8">
          <div>
            <p className="text-sm font-semibold text-gray-700">Composite Score</p>
            <p className="text-4xl font-bold text-indigo-600 mt-2">
              {(sentiment.composite_sentiment_score * 100).toFixed(0)}%
            </p>
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-700 mb-2">Overall Tone</p>
            <p className="text-2xl font-bold text-gray-900">{sentiment.overall_tone}</p>
          </div>
        </div>
      </div>

      {/* Mentions Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Positive Mentions</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{sentiment.positive_mentions}</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Neutral Mentions</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">{sentiment.neutral_mentions}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-gray-700">Negative Mentions</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{sentiment.negative_mentions}</p>
        </div>
      </div>

      {/* Analyst Sentiment */}
      {sentiment.analyst_rating && (
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analyst Rating</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-sm text-gray-700">Rating</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">{sentiment.analyst_rating}</p>
            </div>
            <div>
              <p className="text-sm text-gray-700">Bullish</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{sentiment.bullish_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-700">Neutral</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">{sentiment.neutral_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-700">Bearish</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{sentiment.bearish_count}</p>
            </div>
          </div>
        </div>
      )}

      {/* Market Position */}
      {sentiment.market_share && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <p className="text-sm font-semibold text-gray-700">Market Share</p>
            <p className="text-3xl font-bold text-purple-600 mt-2">{sentiment.market_share.toFixed(2)}%</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <p className="text-sm font-semibold text-gray-700">Brand Strength</p>
            <p className="text-3xl font-bold text-amber-600 mt-2">
              {(sentiment.brand_strength_score * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Industry Tab Component
const IndustryTab = ({ entityId }) => {
  const [industry, setIndustry] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIndustry();
  }, [entityId]);

  const loadIndustry = async () => {
    setLoading(true);
    try {
      // Industry data would come from report sections
      setIndustry({ message: 'Industry intelligence loading...' });
    } catch (err) {
      console.error('Failed to load industry data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 rounded-lg p-6 border border-blue-200 text-center">
      <p className="text-blue-900">Industry intelligence data will be displayed here</p>
    </div>
  );
};

export default ResearchDashboard;
