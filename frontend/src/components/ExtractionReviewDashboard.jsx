import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { extractionService } from '../services/extractionService';
import { aiExtractionService } from '../services/aiExtractionService';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const formatValue = (value, unit) => {
  if (value === null || value === undefined) return '—';
  const num = parseFloat(value);
  if (isNaN(num)) return String(value);

  if (unit === 'INR') {
    if (Math.abs(num) >= 1e7) return `₹${(num / 1e7).toFixed(2)} Cr`;
    if (Math.abs(num) >= 1e5) return `₹${(num / 1e5).toFixed(2)} L`;
    return `₹${num.toLocaleString('en-IN')}`;
  }
  if (unit === '%') return `${num.toFixed(2)}%`;
  if (unit === 'x') return `${num.toFixed(2)}×`;
  if (unit === 'pts') return num.toFixed(1);
  return num.toLocaleString('en-IN', { maximumFractionDigits: 4 });
};

const ConfidenceBadge = ({ confidence }) => {
  if (confidence === 0)
    return <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-500">N/A</span>;

  const pct = Math.round(confidence * 100);
  const [bg, text] =
    confidence >= 0.9  ? ['bg-green-100',  'text-green-700']  :
    confidence >= 0.7  ? ['bg-yellow-100', 'text-yellow-700'] :
    confidence >= 0.5  ? ['bg-orange-100', 'text-orange-700'] :
                         ['bg-red-100',    'text-red-700'];

  return (
    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${bg} ${text}`}>
      {pct}%
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const map = {
    pending:  ['bg-yellow-100 text-yellow-800 border-yellow-200', '⏳ Pending Review'],
    approved: ['bg-green-100 text-green-800 border-green-200',   '✅ Approved'],
    rejected: ['bg-red-100 text-red-800 border-red-200',         '❌ Rejected'],
  };
  const [cls, label] = map[status] || map.pending;
  return (
    <span className={`px-3 py-1 rounded-full border text-sm font-semibold ${cls}`}>
      {label}
    </span>
  );
};

const ConfidenceBar = ({ value, label }) => (
  <div className="flex items-center gap-3">
    <span className="text-xs text-gray-500 w-32 shrink-0">{label}</span>
    <div className="flex-1 bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all ${
          value >= 0.9 ? 'bg-green-500' :
          value >= 0.7 ? 'bg-yellow-400' :
          value >= 0.5 ? 'bg-orange-400' : 'bg-red-400'
        }`}
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
    <span className="text-xs font-semibold text-gray-700 w-10 text-right">
      {Math.round(value * 100)}%
    </span>
  </div>
);

// ---------------------------------------------------------------------------
// Field row component
// ---------------------------------------------------------------------------

const FieldRow = ({ section, fieldKey, field, correctedValue, onChange }) => {
  const hasCorrection =
    correctedValue !== '' &&
    correctedValue !== null &&
    correctedValue !== undefined &&
    String(correctedValue) !== String(field.value ?? '');

  return (
    <tr className={`border-b hover:bg-blue-50/30 transition-colors ${hasCorrection ? 'bg-amber-50' : ''}`}>
      {/* Label */}
      <td className="px-4 py-3 text-sm font-medium text-gray-800 w-48">
        {field.label}
        {field.unit && <span className="ml-1 text-xs text-gray-400">({field.unit})</span>}
      </td>

      {/* Extracted value */}
      <td className="px-4 py-3 text-sm text-gray-600 font-mono w-44">
        {field.value !== null && field.value !== undefined
          ? <span className="text-gray-800">{formatValue(field.value, field.unit)}</span>
          : <span className="italic text-gray-400">Not extracted</span>}
      </td>

      {/* Editable correction */}
      <td className="px-4 py-3 w-52">
        <input
          type="number"
          step="any"
          placeholder={field.value !== null ? String(field.value) : 'Enter value…'}
          value={correctedValue ?? ''}
          onChange={(e) => onChange(section, fieldKey, e.target.value)}
          className={`w-full px-3 py-1.5 border rounded-md text-sm font-mono focus:outline-none focus:ring-2
            ${hasCorrection
              ? 'border-amber-400 focus:ring-amber-300 bg-amber-50'
              : 'border-gray-300 focus:ring-blue-300 bg-white'}`}
        />
        {hasCorrection && (
          <p className="mt-0.5 text-xs text-amber-600 font-medium">✎ Corrected</p>
        )}
      </td>

      {/* Confidence */}
      <td className="px-4 py-3 text-center w-24">
        <ConfidenceBadge confidence={field.confidence} />
      </td>

      {/* Source */}
      <td className="px-4 py-3 text-xs text-gray-400 truncate max-w-[140px]">
        {field.source || '—'}
      </td>
    </tr>
  );
};

// ---------------------------------------------------------------------------
// Summary sidebar card
// ---------------------------------------------------------------------------

const SummaryCard = ({ data, corrections, activeSection }) => {
  const correctedCount = useMemo(() => {
    let n = 0;
    for (const sec of Object.values(corrections)) {
      for (const v of Object.values(sec)) {
        if (v !== '' && v !== null && v !== undefined) n++;
      }
    }
    return n;
  }, [corrections]);

  const sectionConfs = useMemo(() =>
    (data?.sections || []).map((s) => ({
      label: s.section_label,
      conf: s.average_confidence,
    })), [data]);

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Summary</h3>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-blue-700">{data?.total_fields ?? 0}</p>
            <p className="text-xs text-gray-500 mt-0.5">Fields Extracted</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-amber-600">{correctedCount}</p>
            <p className="text-xs text-gray-500 mt-0.5">Corrections Made</p>
          </div>
        </div>
        <div className="mt-3 bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Overall Confidence</p>
          <div className="flex items-end gap-1">
            <p className="text-3xl font-bold text-gray-800">
              {Math.round((data?.overall_confidence ?? 0) * 100)}
            </p>
            <p className="text-lg text-gray-500 mb-0.5">%</p>
          </div>
        </div>
      </div>

      {/* Section confidence breakdown */}
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
          Section Confidence
        </h3>
        <div className="space-y-2">
          {sectionConfs.map(({ label, conf }) => (
            <ConfidenceBar key={label} label={label} value={conf} />
          ))}
        </div>
      </div>

      {/* Info */}
      {data?.created_at && (
        <div className="bg-white border rounded-xl p-4 shadow-sm text-xs text-gray-500 space-y-1">
          <p><span className="font-medium">Result ID:</span> #{data.result_id}</p>
          <p><span className="font-medium">Created:</span>{' '}
            {new Date(data.created_at).toLocaleString()}
          </p>
          {data.reviewed_at && (
            <p><span className="font-medium">Reviewed:</span>{' '}
              {new Date(data.reviewed_at).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export const ExtractionReviewDashboard = ({ entityId, entityName }) => {
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const [data, setData]             = useState(null);
  const [activeSection, setActiveSection] = useState(null);

  // corrections: { [section_key]: { [field_key]: value } }
  const [corrections, setCorrections] = useState({});
  const [reviewNotes, setReviewNotes] = useState('');

  const [submitting, setSubmitting]   = useState(false);
  const [submitResult, setSubmitResult] = useState(null); // { success, message }
  const [processingAll, setProcessingAll] = useState(false);

  // ---- Load results -------------------------------------------------------
  const loadResults = useCallback(async () => {
    if (!entityId) return;
    setLoading(true);
    setError(null);
    setSubmitResult(null);
    try {
      const res = await extractionService.getResults(entityId);
      const result = res.data;
      setData(result);
      setCorrections({});
      setReviewNotes(result.review_notes || '');
      if (result.sections?.length) setActiveSection(result.sections[0].section_key);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load extraction results.');
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  useEffect(() => { loadResults(); }, [loadResults]);

  const handleProcessAllDocuments = async () => {
    if (!entityId) return;
    setProcessingAll(true);
    setSubmitResult(null);
    try {
      const res = await aiExtractionService.batchProcessDocuments(entityId);
      const payload = res.data || {};
      if (payload.status === 'error') {
        throw new Error(payload.message || payload.error || 'Batch processing failed');
      }
      await loadResults();
      setSubmitResult({
        success: true,
        message: `Processed ${payload.documents_processed ?? 0} documents and refreshed extracted fields.`,
      });
    } catch (err) {
      setSubmitResult({
        success: false,
        message: err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to process documents.',
      });
    } finally {
      setProcessingAll(false);
    }
  };

  // ---- Handle inline edit -------------------------------------------------
  const handleFieldChange = (section, fieldKey, value) => {
    setCorrections((prev) => ({
      ...prev,
      [section]: { ...(prev[section] || {}), [fieldKey]: value },
    }));
    setSubmitResult(null);
  };

  // ---- Count corrections --------------------------------------------------
  const correctedCount = useMemo(() => {
    let n = 0;
    for (const sec of Object.values(corrections)) {
      for (const v of Object.values(sec)) {
        if (v !== '' && v !== null && v !== undefined) n++;
      }
    }
    return n;
  }, [corrections]);

  // Build cleaned corrections (remove empty strings)
  const buildCleanedCorrections = () => {
    const out = {};
    for (const [sec, fields] of Object.entries(corrections)) {
      const secOut = {};
      for (const [fk, fv] of Object.entries(fields)) {
        if (fv !== '' && fv !== null && fv !== undefined) {
          secOut[fk] = parseFloat(fv) || fv;
        }
      }
      if (Object.keys(secOut).length) out[sec] = secOut;
    }
    return out;
  };

  // ---- Submit -------------------------------------------------------------
  const handleSubmit = async (approvalStatus) => {
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const res = await extractionService.approve({
        entity_id: entityId,
        result_id: data?.result_id || null,
        corrected_fields: buildCleanedCorrections(),
        review_notes: reviewNotes,
        status: approvalStatus,
      });
      setSubmitResult({ success: true, message: res.data.message });
      // Reload to reflect new status
      await loadResults();
    } catch (err) {
      setSubmitResult({
        success: false,
        message: err.response?.data?.detail || 'Submission failed. Please try again.',
      });
    } finally {
      setSubmitting(false);
    }
  };

  // ---- Current section data -----------------------------------------------
  const currentSection = useMemo(
    () => data?.sections?.find((s) => s.section_key === activeSection),
    [data, activeSection],
  );

  // =========================================================================
  // Render
  // =========================================================================

  if (!entityId) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        Select an entity to review its extraction results.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-500 text-sm">Loading extraction results…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700 flex flex-col gap-3">
        <p className="font-semibold">⚠ Error loading results</p>
        <p className="text-sm">{error}</p>
        <div className="flex items-center gap-2">
          <button
            onClick={handleProcessAllDocuments}
            disabled={processingAll}
            className="self-start px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {processingAll ? 'Processing All…' : 'Process All Documents'}
          </button>
          <button
            onClick={loadResults}
            className="self-start px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-5">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="bg-white border rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Extraction Review
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {data.entity_name || entityName || `Entity #${entityId}`}
              {data.document_id && (
                <span className="ml-2 text-xs text-blue-500">Doc #{data.document_id}</span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={data.status} />
            <button
              onClick={handleProcessAllDocuments}
              disabled={processingAll}
              className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {processingAll ? 'Processing All…' : 'Process All Documents'}
            </button>
            <button
              onClick={loadResults}
              className="text-xs text-blue-600 hover:underline"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Overall confidence bar (wide) */}
        <div className="mt-4">
          <ConfidenceBar
            label="Overall Confidence"
            value={data.overall_confidence || 0}
          />
        </div>
      </div>

      {/* ── Success / error banner ─────────────────────────────────────────── */}
      {submitResult && (
        <div
          className={`p-4 rounded-xl border text-sm font-medium flex items-center gap-2
            ${submitResult.success
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'}`}
        >
          {submitResult.success ? '✅' : '⚠'} {submitResult.message}
        </div>
      )}

      {/* ── Main two-column layout ─────────────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row gap-5">

        {/* ── Left: sections + table ─────────────────────────────────────── */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* Section tabs */}
          <div className="flex gap-1 flex-wrap bg-gray-100 rounded-xl p-1">
            {(data.sections || []).map((sec) => {
              const secCorrections = corrections[sec.section_key] || {};
              const corrCount = Object.values(secCorrections).filter(
                (v) => v !== '' && v !== null && v !== undefined,
              ).length;
              const isActive = activeSection === sec.section_key;
              return (
                <button
                  key={sec.section_key}
                  onClick={() => setActiveSection(sec.section_key)}
                  className={`flex-1 min-w-[110px] px-3 py-2 text-xs font-semibold rounded-lg transition-all
                    ${isActive
                      ? 'bg-white shadow text-blue-700 border border-blue-100'
                      : 'text-gray-600 hover:bg-white/60'}`}
                >
                  {sec.section_label}
                  {corrCount > 0 && (
                    <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4
                      rounded-full bg-amber-500 text-white text-[10px] font-bold">
                      {corrCount}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Fields table */}
          {currentSection && (
            <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                <h3 className="font-semibold text-gray-800 text-sm">
                  {currentSection.section_label}
                </h3>
                <ConfidenceBadge confidence={currentSection.average_confidence} />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="text-xs text-gray-500 bg-gray-50/80 uppercase tracking-wide">
                      <th className="px-4 py-2 font-semibold">Field</th>
                      <th className="px-4 py-2 font-semibold">Extracted Value</th>
                      <th className="px-4 py-2 font-semibold">
                        Correction
                        <span className="ml-1 font-normal normal-case text-gray-400">(editable)</span>
                      </th>
                      <th className="px-4 py-2 font-semibold text-center">Confidence</th>
                      <th className="px-4 py-2 font-semibold">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(currentSection.fields).map(([fieldKey, field]) => (
                      <FieldRow
                        key={fieldKey}
                        section={currentSection.section_key}
                        fieldKey={fieldKey}
                        field={field}
                        correctedValue={corrections[currentSection.section_key]?.[fieldKey] ?? ''}
                        onChange={handleFieldChange}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Review notes + action bar */}
          <div className="bg-white border rounded-xl p-4 shadow-sm space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Review Notes
              </label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add any notes about your corrections or reasons for approval/rejection…"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-300 resize-y"
              />
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <p className="text-sm text-gray-500">
                {correctedCount > 0
                  ? <span className="text-amber-600 font-semibold">{correctedCount} field{correctedCount > 1 ? 's' : ''} corrected</span>
                  : 'No corrections — approving as-is'}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleSubmit('rejected')}
                  disabled={submitting || data.status === 'rejected'}
                  className="px-4 py-2 border border-red-300 text-red-600 text-sm font-semibold
                    rounded-lg hover:bg-red-50 disabled:opacity-40 transition-colors"
                >
                  {submitting ? '…' : '✗ Reject'}
                </button>
                <button
                  onClick={() => handleSubmit('approved')}
                  disabled={submitting || data.status === 'approved'}
                  className="px-5 py-2 bg-blue-600 text-white text-sm font-semibold
                    rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors shadow"
                >
                  {submitting ? 'Saving…' : '✓ Approve Corrections'}
                </button>
              </div>
            </div>
          </div>

          {/* Existing corrections (if already reviewed) */}
          {data.corrected_fields && Object.keys(data.corrected_fields).length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-sm">
              <h4 className="text-sm font-semibold text-amber-800 mb-3">
                Previously Approved Corrections
              </h4>
              {Object.entries(data.corrected_fields).map(([secKey, fields]) => (
                <div key={secKey} className="mb-3">
                  <p className="text-xs font-semibold text-amber-700 uppercase mb-1">{secKey.replace(/_/g, ' ')}</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {Object.entries(fields).map(([fk, fv]) => (
                      <div key={fk} className="text-xs bg-white border border-amber-200 rounded-lg px-2 py-1.5">
                        <span className="text-gray-500 block">{fk.replace(/_/g, ' ')}</span>
                        <span className="font-semibold text-gray-800">{String(fv)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {data.review_notes && (
                <p className="text-xs text-amber-700 mt-2 italic">"{data.review_notes}"</p>
              )}
            </div>
          )}
        </div>

        {/* ── Right: summary sidebar ─────────────────────────────────────── */}
        <div className="w-full lg:w-64 shrink-0">
          <SummaryCard
            data={data}
            corrections={corrections}
            activeSection={activeSection}
          />
        </div>
      </div>
    </div>
  );
};

export default ExtractionReviewDashboard;
