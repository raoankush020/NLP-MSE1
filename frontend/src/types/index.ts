export interface User {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  user_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: 'PENDING' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  error_message?: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  chunks?: DocumentChunk[];
}

export interface RetrievedContextItem {
  source: string;
  page: number;
  chunk_id: string | number;
  similarity: number;
  text: string;
  document_id?: string;
}

export type ClaimClassification = 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'CONTRADICTED';

export interface ClaimItem {
  claim: string;
  classification: ClaimClassification;
  score: number;
  evidence?: string | null;
  conflicting_text?: string | null;
}

export interface HallucinationSummary {
  hallucinated: boolean;
  support_score: number;
  hallucination_score: number;
  classification: 'NOT_HALLUCINATED' | 'LOW_HALLUCINATION' | 'MEDIUM_HALLUCINATION' | 'HIGH_HALLUCINATION';
}

export interface QueryResult {
  query_id: string;
  evaluation_id?: string;
  question: string;
  answer: string;
  retrieved_context: RetrievedContextItem[];
  hallucination: HallucinationSummary;
  claims: ClaimItem[];
  created_at?: string;
}

export interface EvaluationListItem {
  id: string;
  query_id: string;
  question: string;
  support_score: number;
  hallucination_score: number;
  classification: string;
  hallucinated: boolean;
  created_at: string;
}

export interface EvaluationDetail extends EvaluationListItem {
  answer: string;
  retrieved_context: RetrievedContextItem[];
  claims: ClaimItem[];
}

export interface DashboardStats {
  total_documents: number;
  total_queries: number;
  total_evaluations: number;
  grounded_answers: number;
  hallucinated_answers: number;
  average_hallucination_score: number;
  average_support_score: number;
}

export interface DashboardCharts {
  grounded_vs_hallucinated: { name: string; value: number; color: string }[];
  hallucination_rates: { name: string; rate: number }[];
  queries_over_time: { name: string; queries: number }[];
  support_score_distribution: { range: string; count: number }[];
  hallucination_types: { name: string; value: number; color: string }[];
  claim_classifications: { name: string; value: number; color: string }[];
}

export interface UserSettings {
  llm_model: string;
  temperature: number;
  top_k: number;
  chunk_size: number;
  chunk_overlap: number;
  embedding_model: string;
  has_custom_api_key: boolean;
}
