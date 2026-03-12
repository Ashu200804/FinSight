import React, { useState } from 'react';
import { aiExtractionService } from '../services/aiExtractionService';

export const DocumentExtractionProcessor = ({ documentId, entityId, onProcessComplete }) => {
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const handleProcessDocument = async () => {
    setProcessing(true);
    setError(null);

    try {
      const response = await aiExtractionService.processStoredDocument(documentId);
      if (response.data?.status === 'error') {
        throw new Error(response.data?.message || response.data?.error || 'Failed to process document');
      }
      const extractedResults = response.data?.processing_results || response.data;
      if (extractedResults?.status === 'error') {
        throw new Error(extractedResults?.message || extractedResults?.error || 'Failed to process document');
      }
      setResults(extractedResults);
      if (onProcessComplete) {
        onProcessComplete(response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to process document');
    } finally {
      setProcessing(false);
    }
  };

  const formatNumber = (value) => {
    if (typeof value !== 'number') return value;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
    }).format(value);
  };

  if (!results) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Document Extraction</h3>
        <p className="text-gray-600 mb-6">
          This document processing will extract financial data using advanced AI including OCR, table extraction, and consistency checks.
        </p>
        <button
          onClick={handleProcessDocument}
          disabled={processing}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          {processing ? 'Processing...' : 'Process Document'}
        </button>
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}
      </div>
    );
  }

  const extraction = results?.extracted_data || {};
  const validation = results?.validation_results || {};
  const consistency = results?.consistency_results || {};
  const stages = results?.pipeline_stages || {};

  const companyEntries = Object.entries(extraction?.company_info || {}).filter(([, value]) => value !== null && value !== undefined && value !== '');
  const incomeEntries = Object.entries(extraction?.income_statement || {}).filter(([, value]) => value !== null && value !== undefined && value !== '');
  const balanceEntries = Object.entries(extraction?.balance_sheet || {}).filter(([, value]) => value !== null && value !== undefined && value !== '');
  const totalExtractedFields = companyEntries.length + incomeEntries.length + balanceEntries.length;

  return (
    <div className="space-y-6">
      {/* Status Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Status</h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 border rounded-lg">
            <p className="text-sm text-gray-600">Overall Confidence</p>
            <p className="text-2xl font-bold text-blue-600">
              {(results?.overall_confidence * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-sm text-gray-600">Validation Status</p>
            <p className={`text-2xl font-bold ${validation?.validation_passed ? 'text-green-600' : 'text-red-600'}`}>
              {validation?.validation_passed ? '✓ Passed' : '✗ Failed'}
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-sm text-gray-600">Consistency Status</p>
            <p className={`text-2xl font-bold ${consistency?.passed ? 'text-green-600' : 'text-yellow-600'}`}>
              {consistency?.passed ? '✓ All Checks' : `⚠ ${consistency?.summary?.failed || 0} Issues`}
            </p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-sm text-gray-600">Documents Processed</p>
            <p className="text-2xl font-bold text-purple-600">{stages?.table_extraction?.tables_found || 0} Tables</p>
          </div>
        </div>

        {/* Pipeline Progress */}
        <div className="space-y-2">
          <h4 className="font-semibold text-sm text-gray-900">Pipeline Stages</h4>
          <div className="space-y-1 text-sm">
            {Object.entries(stages).map(([stageName, stageData]) => (
              <div key={stageName} className="flex items-center gap-2">
                <svg className="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                </svg>
                <span className="text-gray-700 capitalize">{stageName.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6">
            {['overview', 'company', 'income', 'balance', 'validation', 'consistency'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="rounded-lg border p-4 bg-blue-50">
                  <p className="text-xs text-blue-700 uppercase">Extracted Fields</p>
                  <p className="text-2xl font-bold text-blue-900">{totalExtractedFields}</p>
                </div>
                <div className="rounded-lg border p-4 bg-indigo-50">
                  <p className="text-xs text-indigo-700 uppercase">Company Fields</p>
                  <p className="text-2xl font-bold text-indigo-900">{companyEntries.length}</p>
                </div>
                <div className="rounded-lg border p-4 bg-emerald-50">
                  <p className="text-xs text-emerald-700 uppercase">Income Fields</p>
                  <p className="text-2xl font-bold text-emerald-900">{incomeEntries.length}</p>
                </div>
                <div className="rounded-lg border p-4 bg-purple-50">
                  <p className="text-xs text-purple-700 uppercase">Balance Fields</p>
                  <p className="text-2xl font-bold text-purple-900">{balanceEntries.length}</p>
                </div>
              </div>

              {totalExtractedFields === 0 ? (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
                  No structured financial fields were extracted from this document yet.
                </div>
              ) : (
                <div className="rounded-lg border border-gray-200 overflow-hidden">
                  <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 font-semibold text-gray-900">
                    Extracted Values
                  </div>
                  <div className="divide-y divide-gray-100">
                    {[...companyEntries, ...incomeEntries, ...balanceEntries].map(([key, value]) => (
                      <div key={key} className="px-4 py-3 flex items-center justify-between text-sm">
                        <span className="text-gray-600 uppercase tracking-wide">{key.replace(/_/g, ' ')}</span>
                        <span className="font-semibold text-gray-900">{typeof value === 'number' ? formatNumber(value) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Company Info Tab */}
          {activeTab === 'company' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Company Information</h4>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(extraction?.company_info || {}).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-xs text-gray-600 uppercase">{key.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900">{value || '-'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Income Statement Tab */}
          {activeTab === 'income' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Income Statement</h4>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(extraction?.income_statement || {}).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-xs text-gray-600 uppercase">{key.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900">{value ? formatNumber(value) : '-'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Balance Sheet Tab */}
          {activeTab === 'balance' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Balance Sheet</h4>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(extraction?.balance_sheet || {}).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-xs text-gray-600 uppercase">{key.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900">{value ? formatNumber(value) : '-'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Validation Tab */}
          {activeTab === 'validation' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Validation Results</h4>
              <div className="space-y-2">
                {validation?.validations?.map((val, idx) => (
                  <div key={idx} className="p-3 border rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{val.field}</p>
                        <p className="text-sm text-gray-600">{val.reason}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        val.validation_status === 'valid' ? 'bg-green-100 text-green-800' :
                        val.validation_status === 'invalid' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {val.validation_status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Confidence: {(val.confidence * 100).toFixed(0)}%</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Consistency Tab */}
          {activeTab === 'consistency' && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Financial Consistency Checks</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-600">Total Checks</p>
                  <p className="text-2xl font-bold text-blue-900">{consistency?.summary?.total_checks}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-600">Passed</p>
                  <p className="text-2xl font-bold text-green-900">{consistency?.summary?.passed}</p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg">
                  <p className="text-xs text-red-600">Failed</p>
                  <p className="text-2xl font-bold text-red-900">{consistency?.summary?.failed}</p>
                </div>
                <div className="p-3 bg-yellow-50 rounded-lg">
                  <p className="text-xs text-yellow-600">Warnings</p>
                  <p className="text-2xl font-bold text-yellow-900">{consistency?.summary?.warnings}</p>
                </div>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {consistency?.checks?.map((check, idx) => (
                  <div key={idx} className={`p-3 border rounded-lg ${
                    check.status === 'pass' ? 'border-green-200 bg-green-50' :
                    check.status === 'fail' ? 'border-red-200 bg-red-50' :
                    'border-yellow-200 bg-yellow-50'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{check.check_name}</p>
                        <p className="text-sm text-gray-600">{check.message}</p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        check.status === 'pass' ? 'bg-green-200 text-green-800' :
                        check.status === 'fail' ? 'bg-red-200 text-red-800' :
                        'bg-yellow-200 text-yellow-800'
                      }`}>
                        {check.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Severity: {check.severity}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentExtractionProcessor;
