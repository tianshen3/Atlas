'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { uploadDocument, listDocuments, deleteDocument } from '@/lib/api/documents';
import { DocumentResponse } from '@/lib/api/types';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2 
} from 'lucide-react';

export const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  
  // Accessible delete confirmation state
  const [docToDelete, setDocToDelete] = useState<{ id: string; filename: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const confirmCancelBtnRef = useRef<HTMLButtonElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await listDocuments(0, 50);
      setDocuments(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve document repository');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load on mount
  useEffect(() => {
    let isMounted = true;
    listDocuments(0, 50)
      .then((res) => {
        if (isMounted) {
          setDocuments(res.items || []);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to retrieve document repository');
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Adaptive polling: Check every 3s if any doc is in PENDING or PROCESSING status
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

  // Handle focus trapping in modal when open
  useEffect(() => {
    if (docToDelete) {
      confirmCancelBtnRef.current?.focus();
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          setDocToDelete(null);
        }
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [docToDelete]);

  const processSelectedFile = async (file: File) => {
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Unsupported format. Only PDF documents are accepted.');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError('File exceeds the 50 MB upload threshold.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const uploaded = await uploadDocument(file);
      setSuccessMsg(`Document '${uploaded.filename}' staged. Ingestion worker dispatched.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await fetchDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const confirmDelete = async () => {
    if (!docToDelete) return;
    const { id, filename } = docToDelete;

    try {
      await deleteDocument(id);
      setSuccessMsg(`Document '${filename}' deleted.`);
      setDocToDelete(null);
      await fetchDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deletion failed.');
      setDocToDelete(null);
    }
  };

  const renderStatus = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#6F9B82]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#6F9B82]" aria-hidden="true" />
            <span>Indexed</span>
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#89938C]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#89938C] animate-pulse" aria-hidden="true" />
            <span>Processing...</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#C26363]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C26363]" aria-hidden="true" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#626B65]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#626B65]" aria-hidden="true" />
            <span>Pending</span>
          </span>
        );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <section aria-labelledby="doc-store-heading" className="w-full max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 pb-2 border-b border-[#242A26]">
        <div>
          <h2 id="doc-store-heading" className="text-base font-semibold text-[#E4E8E4] tracking-tight">
            Document Store
          </h2>
          <p className="text-xs text-[#89938C] mt-0.5">
            Manage documents available to the ATLAS knowledge base.
          </p>
        </div>

        <button
          onClick={() => fetchDocs()}
          className="self-start flex items-center gap-1.5 text-xs text-[#89938C] hover:text-[#E4E8E4] font-mono px-2 py-1 rounded hover:bg-[#151A17] transition-colors"
          aria-label="Refresh document repository"
        >
          <RefreshCw className="w-3 h-3" aria-hidden="true" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div 
          role="alert" 
          aria-live="assertive"
          className="p-3 bg-[#1F1414] border border-[#522525] text-[#E08A8A] text-xs rounded flex items-start gap-2.5"
        >
          <AlertCircle className="w-4 h-4 text-[#E08A8A] shrink-0 mt-0.5" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div 
          role="status" 
          aria-live="polite"
          className="p-3 bg-[#121A15] border border-[#243E2E] text-[#82AA91] text-xs rounded flex items-start gap-2.5"
        >
          <CheckCircle2 className="w-4 h-4 text-[#82AA91] shrink-0 mt-0.5" aria-hidden="true" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload Zone (Compact & Functional) */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`p-6 border border-dashed rounded-md text-center transition-colors ${
          isDragOver 
            ? 'bg-[#151A17] border-[#6F9B82]' 
            : 'bg-[#111513] border-[#242A26] hover:border-[#343C37]'
        }`}
      >
        <div className="flex flex-col items-center justify-center space-y-2">
          <UploadCloud className="w-6 h-6 text-[#6F9B82]" aria-hidden="true" />
          
          <div className="space-y-1">
            <p className="text-xs font-mono font-semibold tracking-wider text-[#E4E8E4] uppercase">
              DROP PDF HERE
            </p>
            <p className="text-[11px] text-[#89938C]">
              or choose a file from your system
            </p>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <input
              type="file"
              accept=".pdf,application/pdf"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              className="sr-only"
              id="pdf-file-upload-input"
            />
            <label
              htmlFor="pdf-file-upload-input"
              className={`px-3 py-1.5 bg-[#151A17] hover:bg-[#1C221F] text-[#E4E8E4] border border-[#242A26] hover:border-[#6F9B82] rounded text-xs font-mono uppercase tracking-wider font-medium cursor-pointer transition-colors ${
                uploading ? 'opacity-50 pointer-events-none' : ''
              }`}
            >
              {uploading ? 'Staging...' : 'Choose PDF File'}
            </label>

            <span className="text-[10px] font-mono text-[#626B65] uppercase">
              PDF · MAX 50 MB
            </span>
          </div>
        </div>
      </div>

      {/* Document Catalog Table */}
      <div className="bg-[#111513] border border-[#242A26] rounded-md overflow-hidden">
        <div className="px-4 py-3 border-b border-[#242A26] flex items-center justify-between text-xs">
          <span className="font-mono text-[11px] text-[#89938C] uppercase tracking-wider font-semibold">
            INDEXED CORPUS ({documents.length})
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs font-mono text-[#89938C]" role="status">
            Loading document metadata...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#89938C]">
            No documents available. Upload a PDF document above to index into the knowledge base.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" aria-label="Documents catalog table">
              <thead className="bg-[#151A17] border-b border-[#242A26] text-[#89938C] font-mono text-[10px] uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-4 py-2.5">Name</th>
                  <th scope="col" className="px-4 py-2.5">Size</th>
                  <th scope="col" className="px-4 py-2.5">Status</th>
                  <th scope="col" className="px-4 py-2.5">Uploaded</th>
                  <th scope="col" className="px-4 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#242A26] text-[#E4E8E4]">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-[#151A17]/50 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-[#6F9B82] shrink-0" aria-hidden="true" />
                        <span className="truncate max-w-xs sm:max-w-md">{doc.filename}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-[#89938C] text-[11px]">
                      {formatFileSize(doc.file_size_bytes)}
                    </td>
                    <td className="px-4 py-3">
                      {renderStatus(doc.status)}
                    </td>
                    <td className="px-4 py-3 font-mono text-[#89938C] text-[11px]">
                      {new Date(doc.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setDocToDelete({ id: doc.id, filename: doc.filename })}
                        aria-label={`Delete ${doc.filename}`}
                        className="text-[#89938C] hover:text-[#C26363] p-1 rounded hover:bg-[#151A17] transition-colors focus:ring-1 focus:ring-[#C26363]"
                      >
                        <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Accessible Confirmation Modal for Deletion (WCAG 2.2 AA) */}
      {docToDelete && (
        <div 
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-desc"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs"
        >
          <div className="w-full max-w-md bg-[#111513] border border-[#242A26] rounded-md p-6 shadow-2xl space-y-4">
            <h3 id="delete-dialog-title" className="text-sm font-semibold text-[#E4E8E4]">
              Confirm Document Removal
            </h3>
            <p id="delete-dialog-desc" className="text-xs text-[#89938C] leading-relaxed">
              Are you sure you want to remove <span className="text-[#E4E8E4] font-medium font-mono">{docToDelete.filename}</span>? This permanently purges the raw file, relational chunks, and Qdrant vector embeddings.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                ref={confirmCancelBtnRef}
                type="button"
                onClick={() => setDocToDelete(null)}
                className="px-3 py-1.5 bg-[#151A17] hover:bg-[#1C221F] text-[#89938C] hover:text-[#E4E8E4] border border-[#242A26] rounded text-xs font-mono uppercase"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                className="px-3 py-1.5 bg-[#2A1717] hover:bg-[#3A1D1D] text-[#E08A8A] border border-[#522525] rounded text-xs font-mono uppercase font-semibold"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
