// Shared API types mirroring the FastAPI response schemas.

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface DocumentItem {
  id: number;
  filename: string;
  format: string;
  content_type: string;
  status: 'processing' | 'ready' | 'failed';
  collection_id: number | null;
  owner_id: number | null;
  version: number;
  num_chunks: number;
  error: string;
  created_at: string;
}

export interface DocumentList {
  items: DocumentItem[];
  total: number;
}

export interface Collection {
  id: number;
  name: string;
  description: string;
  owner_id: number | null;
  created_at: string;
  document_count: number;
}

export interface CollectionDetail extends Collection {
  documents: DocumentItem[];
}

export interface Citation {
  marker: string;
  chunk_id: number | null;
  document_id: number | null;
  filename: string | null;
  page: number | null;
  score: number;
  snippet: string;
}

export interface Highlight {
  term: string;
  start: number;
  end: number;
}

export interface SourceDocument {
  document_id: number | null;
  filename: string | null;
  page: number | null;
  collection_id: number | null;
}

export interface AnswerResponse {
  question: string;
  answer: string;
  confidence: number;
  citations: Citation[];
  highlights: Highlight[];
  source_document: SourceDocument | null;
}

export interface SearchResultItem {
  chunk_id: number | null;
  document_id: number | null;
  filename: string | null;
  page: number | null;
  chunk_index: number | null;
  score: number;
  text: string;
}

export interface SearchResults {
  query: string;
  mode: string;
  results: SearchResultItem[];
}

export interface AnalyticsOverview {
  documents: number;
  collections: number;
  chunks: number;
  users: number;
  queries: number;
  ready_documents: number;
}

export interface UsageStats {
  recent_queries: { question: string; confidence: number; created_at: string }[];
  top_documents: { document_id: number; filename: string; chunks: number }[];
}
