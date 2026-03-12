import React, { useEffect, useState } from 'react';
import { documentService } from '../services/documentService';

export const RequiredDocuments = ({ entityId }) => {
  const [requiredDocs, setRequiredDocs] = useState([]);
  const [uploadedDocs, setUploadedDocs] = useState({});
  const [loading, setLoading] = useState(true);

  const REQUIRED_DOCUMENTS = [
    'ALM',
    'Shareholding Pattern',
    'Borrowing Profile',
    'Annual Reports',
    'Portfolio Performance',
  ];

  useEffect(() => {
    fetchRequiredDocumentsStatus();
  }, [entityId]);

  const fetchRequiredDocumentsStatus = async () => {
    try {
      setLoading(true);
      const response = await documentService.getEntityDocuments(entityId);
      const docs = response.data.documents || [];

      // Create a map of uploaded documents
      const uploadedMap = {};
      docs.forEach((doc) => {
        uploadedMap[doc.document_type] = doc;
      });

      setUploadedDocs(uploadedMap);
      setRequiredDocs(REQUIRED_DOCUMENTS);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setLoading(false);
    }
  };

  const calculateCompletionPercentage = () => {
    const uploaded = Object.keys(uploadedDocs).length;
    return Math.round((uploaded / REQUIRED_DOCUMENTS.length) * 100);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600 text-center">Loading required documents...</p>
      </div>
    );
  }

  const completionPercentage = calculateCompletionPercentage();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Required Documents</h3>
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm text-gray-600">
            {Object.keys(uploadedDocs).length} of {REQUIRED_DOCUMENTS.length} documents uploaded
          </p>
          <span className="text-sm font-semibold text-blue-600">{completionPercentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${
              completionPercentage === 100 ? 'bg-green-600' : 'bg-blue-600'
            }`}
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        {REQUIRED_DOCUMENTS.map((docType) => {
          const isUploaded = !!uploadedDocs[docType];
          const doc = uploadedDocs[docType];

          return (
            <div
              key={docType}
              className={`flex items-center justify-between p-4 border rounded-lg transition-colors ${
                isUploaded
                  ? 'border-green-200 bg-green-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-3 flex-1">
                {isUploaded ? (
                  <svg
                    className="h-6 w-6 text-green-600 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <div className="h-6 w-6 border-2 border-gray-300 rounded-full flex-shrink-0 flex items-center justify-center">
                    <span className="text-xs text-gray-400">○</span>
                  </div>
                )}

                <div className="flex-1">
                  <p
                    className={`font-medium ${
                      isUploaded ? 'text-green-900' : 'text-gray-900'
                    }`}
                  >
                    {docType}
                  </p>
                  {isUploaded && doc && (
                    <p className="text-xs text-gray-600 mt-1">
                      Uploaded: {new Date(doc.upload_time).toLocaleDateString()} • v{doc.version}
                    </p>
                  )}
                </div>
              </div>

              {isUploaded && (
                <div className="text-right ml-4">
                  <span className="inline-block px-3 py-1 bg-green-200 text-green-800 text-xs font-semibold rounded-full">
                    Uploaded
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {completionPercentage === 100 && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 text-sm font-medium">
            ✓ All required documents have been uploaded successfully.
          </p>
        </div>
      )}
    </div>
  );
};

export default RequiredDocuments;
