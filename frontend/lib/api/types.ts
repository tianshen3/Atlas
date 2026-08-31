export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface DocumentResponse {
  id: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_hash: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
}

export interface DocumentListResponse {
  items: DocumentResponse[];
  total: number;
}

export interface CitationSource {
  source_index: number;
  document_id: string;
  chunk_id: string;
  file_name: string;
  page_number: number | string;
  score: number;
}

export interface ChatRequest {
  query: string;
  tenant_id: string;
  document_id?: string;
  top_k?: number;
  model?: string;
}

export interface ChatResponse {
  query: string;
  answer: string;
  sources: CitationSource[];
  model_used: string;
  provider_used: string;
  total_sources: number;
}
