'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { uploadDocument, listDocuments, deleteDocument } from '@/lib/api/documents';
import { DocumentResponse } from '@/lib/api/types';

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await listDocuments(0, 50);
      setDocuments(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // Polling logic: Check every 3 seconds if any document is in PENDING or PROCESSING status
  useEffect(() => {
    const hasPending = documents.some(
      (doc) => doc.status === 'PENDING' || doc.status === 'PROCESSING'
    );

    if (!hasPending) return;

    const interval = setInterval(() => {
      fetchDocs();
    }, 3000);

    return () => clearInterval(interval);
  }, [documents, fetchDocs]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
      setError('Only PDF files are supported.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const uploaded = await uploadDocument(file);
      setSuccessMsg(`Document '${uploaded.filename}' uploaded successfully. Ingestion queued.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await fetchDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete '${filename}'?`)) return;

    try {
      await deleteDocument(docId);
      setSuccessMsg(`Document '${filename}' deleted.`);
      await fetchDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document.');
    }
  };

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-green-50 text-green-700 border border-green-200">COMPLETED</span>;
      case 'PROCESSING':
        return <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">PROCESSING...</span>;
      case 'FAILED':
        return <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-red-50 text-red-700 border border-red-200">FAILED</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-yellow-50 text-yellow-700 border border-yellow-200">PENDING</span>;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Document Store</h2>
          <p className="text-xs text-gray-500 mt-1">
            Upload PDF files to ingest into vector storage for grounded RAG query completions.
          </p>
        </div>

        <div>
          <input
            type="file"
            accept=".pdf,application/pdf"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
            id="pdf-upload-input"
          />
          <label
            htmlFor="pdf-upload-input"
            className={`inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800 cursor-pointer transition-colors ${
              uploading ? 'opacity-50 pointer-events-none' : ''
            }`}
          >
            {uploading ? 'Uploading PDF...' : 'Upload PDF Document'}
          </label>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-md">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 text-xs rounded-md">
          {successMsg}
        </div>
      )}

      {/* Documents Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900">
            Uploaded Documents ({documents.length})
          </h3>
          <button
            onClick={() => fetchDocs()}
            className="text-xs text-gray-600 hover:text-gray-900 underline"
          >
            Refresh List
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-gray-500">Loading document catalog...</div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-500">
            No documents uploaded yet. Click above to upload your first PDF.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 border-b border-gray-200 text-gray-600 font-medium">
                <tr>
                  <th className="px-6 py-3">Filename</th>
                  <th className="px-6 py-3">Size</th>
                  <th className="px-6 py-3">Uploaded At</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-gray-800">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3.5 font-medium text-gray-900">{doc.filename}</td>
                    <td className="px-6 py-3.5 text-gray-500 font-mono">{formatFileSize(doc.file_size_bytes)}</td>
                    <td className="px-6 py-3.5 text-gray-500 font-mono">
                      {new Date(doc.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3.5">{renderStatusBadge(doc.status)}</td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="text-red-600 hover:text-red-800 font-medium text-xs hover:underline"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
