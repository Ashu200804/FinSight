import React, { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';

export const FilePreview = ({ documentId, onClose }) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPreview();
  }, [documentId]);

  const fetchPreview = async () => {
    try {
      setLoading(true);
      const response = await documentService.getDocumentPreview(documentId);
      setPreview(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load preview');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-3xl w-full max-h-96 overflow-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {preview?.file_name || 'Preview'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {!loading && preview && (
            <>
              {preview.preview_type === 'image' && (
                <div>
                  <img
                    src={preview.preview_data}
                    alt="Preview"
                    className="max-w-full max-h-96 mx-auto rounded-lg"
                  />
                </div>
              )}

              {preview.preview_type === 'pdf' && (
                <div>
                  <iframe
                    src={preview.preview_data}
                    className="w-full rounded-lg"
                    style={{ height: '400px' }}
                    title="PDF Preview"
                  />
                </div>
              )}

              {preview.preview_type === 'spreadsheet' && (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-16 w-16 text-gray-400 mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="text-gray-600 mb-2">Spreadsheet file preview not available</p>
                  <p className="text-gray-500 text-sm">Download file to view contents</p>
                </div>
              )}

              {preview.preview_type === 'unknown' && (
                <div className="text-center py-12">
                  <p className="text-gray-600">{preview.message}</p>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">File Size</p>
                    <p className="font-medium text-gray-900">
                      {formatFileSize(preview.file_size)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">File Type</p>
                    <p className="font-medium text-gray-900">{preview.mime_type}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Document ID</p>
                    <p className="font-medium text-gray-900">#{preview.id}</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilePreview;
