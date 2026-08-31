import { apiFetch } from './client';
import { DocumentResponse, DocumentListResponse } from './types';

export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetch<DocumentResponse>('/documents/', {
    method: 'POST',
    body: formData,
  });
}

export async function listDocuments(skip = 0, limit = 50): Promise<DocumentListResponse> {
  return apiFetch<DocumentListResponse>(`/documents/?skip=${skip}&limit=${limit}`, {
    method: 'GET',
  });
}

export async function getDocument(documentId: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/documents/${documentId}`, {
    method: 'GET',
  });
}

export async function deleteDocument(documentId: string): Promise<void> {
  return apiFetch<void>(`/documents/${documentId}`, {
    method: 'DELETE',
  });
}
