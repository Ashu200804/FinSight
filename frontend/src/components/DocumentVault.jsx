import React, { useEffect, useState } from 'react';
import { documentService } from '../services/documentService';
import { aiExtractionService } from '../services/aiExtractionService';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import RequiredDocuments from './RequiredDocuments';
import DocumentExtractionProcessor from './DocumentExtractionProcessor';

export const DocumentVault = ({ entityId, onNavigateToReview }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [processingAll, setProcessingAll] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await documentService.getEntityDocuments(entityId);
      setDocuments(response.data.documents || []);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [entityId]);

  const handleUploadSuccess = () => {
    fetchDocuments();
  };

  const handleDelete = (documentId) => {
    setDocuments(documents.filter((doc) => doc.id !== documentId));
  };

  const handleDocumentSelect = (documentId) => {
    setSelectedDocumentId(documentId);
  };

  const handleProcessComplete = (results) => {
    console.log('Processing complete:', results);
    // You can add logic here to refresh documents or show success message
  };

  const handleProcessAllAndReview = async () => {
    if (!entityId) return;
    setProcessingAll(true);
    setProcessingMessage('');

    try {
      const response = await aiExtractionService.batchProcessDocuments(entityId);
      const payload = response?.data || {};
      if (payload.status === 'error') {
        throw new Error(payload.message || payload.error || 'Batch processing failed');
      }

      const processedCount = payload.documents_processed ?? 0;
      setProcessingMessage(`Processed ${processedCount} document${processedCount === 1 ? '' : 's'} successfully. Opening Extraction Review...`);

      if (onNavigateToReview) {
        onNavigateToReview();
      }
    } catch (err) {
      setProcessingMessage(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to process all documents.');
    } finally {
      setProcessingAll(false);
    }
  };

  return (
    <div className="space-y-6">
      <RequiredDocuments entityId={entityId} />

      {!selectedDocumentId ? (
        <>
          <DocumentUpload entityId={entityId} onUploadSuccess={handleUploadSuccess} />

          <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-gray-900">Process Uploaded Documents</p>
                <p className="text-xs text-gray-600">Run extraction for all uploaded documents and jump to Extraction Review.</p>
              </div>
              <button
                onClick={handleProcessAllAndReview}
                disabled={processingAll || loading || documents.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 text-sm font-medium"
              >
                {processingAll ? 'Processing...' : 'Process All & Review'}
              </button>
            </div>
            {processingMessage && (
              <p className={`mt-3 text-sm ${processingMessage.toLowerCase().includes('failed') ? 'text-red-700' : 'text-green-700'}`}>
                {processingMessage}
              </p>
            )}
          </div>

          {loading && (
            <div className="text-center py-12">
              <div className="inline-block">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
              <p className="mt-4 text-gray-600">Loading documents...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {!loading && <DocumentList documents={documents} onDelete={handleDelete} onDocumentSelect={handleDocumentSelect} />}
        </>
      ) : (
        <div className="space-y-4">
          <button
            onClick={() => setSelectedDocumentId(null)}
            className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Documents
          </button>
          <DocumentExtractionProcessor 
            documentId={selectedDocumentId}
            entityId={entityId}
            onProcessComplete={handleProcessComplete}
          />
        </div>
      )}
    </div>
  );
};

export default DocumentVault;
