from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ----------------- Auth Schemas -----------------
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Document Schemas -----------------
class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    page_number: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []

# ----------------- RAG & Query Schemas -----------------
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_ids: Optional[List[str]] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = None

class RetrievedContextItem(BaseModel):
    source: str
    page: int
    chunk_id: Any
    similarity: float
    text: str
    document_id: Optional[str] = None

class ClaimEvaluationItem(BaseModel):
    claim: str
    classification: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED
    score: float         # 1.0, 0.5, 0.0, 0.0
    evidence: Optional[str] = None
    conflicting_text: Optional[str] = None

class HallucinationSummary(BaseModel):
    hallucinated: bool
    support_score: float
    hallucination_score: float
    classification: str

class QueryResponse(BaseModel):
    query_id: str
    evaluation_id: Optional[str] = None
    question: str
    answer: str
    retrieved_context: List[RetrievedContextItem]
    hallucination: HallucinationSummary
    claims: List[ClaimEvaluationItem]
    created_at: Optional[datetime] = None

# ----------------- Evaluation Schemas -----------------
class EvaluateDirectRequest(BaseModel):
    question: str
    answer: str
    context: str

class EvaluationListItem(BaseModel):
    id: str
    query_id: str
    question: str
    support_score: float
    hallucination_score: float
    classification: str
    hallucinated: bool
    created_at: datetime

class EvaluationDetailResponse(BaseModel):
    id: str
    query_id: str
    question: str
    answer: str
    support_score: float
    hallucination_score: float
    classification: str
    hallucinated: bool
    created_at: datetime
    retrieved_context: List[RetrievedContextItem]
    claims: List[ClaimEvaluationItem]

# ----------------- Dashboard & Analytics Schemas -----------------
class DashboardStatsResponse(BaseModel):
    total_documents: int
    total_queries: int
    total_evaluations: int
    grounded_answers: int
    hallucinated_answers: int
    average_hallucination_score: float
    average_support_score: float

class ChartDataPoint(BaseModel):
    name: str
    value: float
    count: Optional[int] = None

class DashboardChartsResponse(BaseModel):
    grounded_vs_hallucinated: List[Dict[str, Any]]
    hallucination_rates: List[Dict[str, Any]]
    queries_over_time: List[Dict[str, Any]]
    support_score_distribution: List[Dict[str, Any]]
    hallucination_types: List[Dict[str, Any]]
    claim_classifications: List[Dict[str, Any]]

# ----------------- Settings Schemas -----------------
class UserSettingsDTO(BaseModel):
    llm_model: str = "extractive-grounded"
    temperature: float = 0.2
    top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    has_custom_api_key: bool = False

class UpdateSettingsRequest(BaseModel):
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_model: Optional[str] = None
    custom_api_key: Optional[str] = None

# Resolve forward references
TokenResponse.model_rebuild()
