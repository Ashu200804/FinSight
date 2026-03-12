import React, { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';

export const DocumentUpload = ({ entityId, onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedDocType, setSelectedDocType] = useState('ALM');
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [supportedTypes, setSupportedTypes] = useState({
    required_documents: [],
    supported_formats: [],
  });

  const SUPPORTED_MIME_TYPES = {
    'application/pdf': 'PDF',
    'application/vnd.ms-excel': 'Excel (.xls)',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel (.xlsx)',
    'text/csv': 'CSV',
    'image/jpeg': 'JPEG',
    'image/png': 'PNG',
    'image/gif': 'GIF',
    'image/webp': 'WebP',
  };

  useEffect(() => {
    // Fetch supported document types
    documentService
      .getSupportedDocumentTypes()
      .then((response) => {
        setSupportedTypes(response.data);
      })
      .catch((err) => console.error('Failed to fetch supported types:', err));
  }, []);

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleFileSelection = async (file) => {
    setError(null);
    setSelectedFile(file);

    // Validate file size
    if (file.size > 100 * 1024 * 1024) {
      setError('File size exceeds 100MB limit');
      setSelectedFile(null);
      return;
    }

    // Validate file type
    if (!SUPPORTED_MIME_TYPES[file.type]) {
      setError(`File type not supported. Supported types: ${Object.values(SUPPORTED_MIME_TYPES).join(', ')}`);
      setSelectedFile(null);
      return;
    }

    // Generate preview
    generateFilePreview(file);
  };

  const generateFilePreview = (file) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      if (file.type.startsWith('image/')) {
        setFilePreview({
          type: 'image',
          data: e.target.result,
          fileName: file.name,
          fileSize: file.size,
          mimeType: file.type,
        });
      } else if (file.type === 'application/pdf') {
        setFilePreview({
          type: 'pdf',
          data: e.target.result,
          fileName: file.name,
          fileSize: file.size,
          mimeType: file.type,
        });
      } else if (file.type === 'text/csv' || SUPPORTED_MIME_TYPES[file.type]?.includes('Excel')) {
        setFilePreview({
          type: 'spreadsheet',
          fileName: file.name,
          fileSize: file.size,
          mimeType: file.type,
        });
      }
    };

    if (file.type.startsWith('image/') || file.type === 'application/pdf') {
      reader.readAsDataURL(file);
    } else {
      setFilePreview({
        type: 'spreadsheet',
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type,
      });
    }
  };

  const uploadFile = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      await documentService.uploadDocument(selectedFile, entityId, selectedDocType);
      setUploadProgress(100);

      // Reset after success
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
        setSelectedFile(null);
        setFilePreview(null);
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      }, 1000);
    } catch (err) {
      setError(`Failed to upload file: ${err.response?.data?.detail || err.message}`);
      setUploading(false);
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
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Required Document Type
          </label>
          <select
            value={selectedDocType}
            onChange={(e) => setSelectedDocType(e.target.value)}
            disabled={uploading || !!selectedFile}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            {supportedTypes.required_documents.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          } ${uploading || selectedFile ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <div className="mb-4">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-14-7v13m0 0l4-4m-4 4l-4-4"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <p className="text-gray-700 font-medium">Drag and drop your document here</p>
          <p className="text-gray-500 text-sm mt-1">or</p>

          <label className="inline-block mt-2">
            <input
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading || !!selectedFile}
              accept={Object.keys(SUPPORTED_MIME_TYPES).join(',')}
            />
            <span className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
              Click to browse
            </span>
          </label>

          <p className="text-gray-500 text-xs mt-2">
            Max size: 100MB | Supported: PDF, Excel, CSV, Images
          </p>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {uploading && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">Uploading: {uploadProgress}%</p>
          </div>
        )}
      </div>

      {filePreview && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">File Preview</h4>

          {filePreview.type === 'image' && (
            <div className="space-y-4">
              <img
                src={filePreview.data}
                alt="Preview"
                className="max-h-96 max-w-full mx-auto rounded-lg"
              />
              <div className="text-sm text-gray-600">
                <p>
                  <strong>File:</strong> {filePreview.fileName}
                </p>
                <p>
                  <strong>Size:</strong> {formatFileSize(filePreview.fileSize)}
                </p>
              </div>
            </div>
          )}

          {filePreview.type === 'pdf' && (
            <div className="space-y-4">
              <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                <p className="text-gray-600 mb-2">📄 PDF Preview (click below to open)</p>
                <iframe
                  src={filePreview.data}
                  className="w-full rounded-lg"
                  style={{ height: '400px' }}
                  title="PDF Preview"
                />
              </div>
              <div className="text-sm text-gray-600">
                <p>
                  <strong>File:</strong> {filePreview.fileName}
                </p>
                <p>
                  <strong>Size:</strong> {formatFileSize(filePreview.fileSize)}
                </p>
              </div>
            </div>
          )}

          {filePreview.type === 'spreadsheet' && (
            <div className="space-y-4">
              <div className="border border-gray-300 rounded-lg p-6 bg-gray-50 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 mb-2"
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
                <p className="text-gray-600">Spreadsheet file preview not available in browser</p>
                <p className="text-gray-500 text-sm mt-1">Download to view contents</p>
              </div>
              <div className="text-sm text-gray-600">
                <p>
                  <strong>File:</strong> {filePreview.fileName}
                </p>
                <p>
                  <strong>Size:</strong> {formatFileSize(filePreview.fileSize)}
                </p>
                <p>
                  <strong>Type:</strong> {SUPPORTED_MIME_TYPES[filePreview.mimeType]}
                </p>
              </div>
            </div>
          )}

          <div className="mt-4 flex gap-3">
            <button
              onClick={() => {
                setSelectedFile(null);
                setFilePreview(null);
              }}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={uploadFile}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Confirm & Upload
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;

