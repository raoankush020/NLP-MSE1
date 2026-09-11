from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum
)
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("QueryRecord", back_populates="user", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(32), default="PENDING")  # PENDING, PROCESSING, INDEXED, FAILED
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("Document", back_populates="chunks")


class QueryRecord(Base):
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="queries")
    retrieved_chunks = relationship("RetrievedChunk", back_populates="query", cascade="all, delete-orphan")
    evaluation = relationship("Evaluation", back_populates="query", uselist=False, cascade="all, delete-orphan")


class RetrievedChunk(Base):
    __tablename__ = "retrieved_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    query_id = Column(String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), nullable=True)
    chunk_id = Column(String(64), nullable=True)
    source = Column(String(255), nullable=False)
    page = Column(Integer, default=1)
    similarity = Column(Float, default=0.0)
    text = Column(Text, nullable=False)

    # Relationships
    query = relationship("QueryRecord", back_populates="retrieved_chunks")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    query_id = Column(String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    support_score = Column(Float, nullable=False)  # 0.0 to 1.0
    hallucination_score = Column(Float, nullable=False)  # 1.0 - support_score
    classification = Column(String(64), nullable=False)  # NOT_HALLUCINATED, LOW_HALLUCINATION, MEDIUM_HALLUCINATION, HIGH_HALLUCINATION
    hallucinated = Column(Boolean, default=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    query = relationship("QueryRecord", back_populates="evaluation")
    user = relationship("User", back_populates="evaluations")
    claims = relationship("Claim", back_populates="evaluation", cascade="all, delete-orphan")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    classification = Column(String(32), nullable=False)  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED
    score = Column(Float, nullable=False)  # 1.0, 0.5, 0.0, 0.0
    evidence = Column(Text, nullable=True)
    conflicting_text = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="claims")


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    llm_model = Column(String(64), default="extractive-grounded")
    temperature = Column(Float, default=0.2)
    top_k = Column(Integer, default=4)
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    embedding_model = Column(String(64), default="all-MiniLM-L6-v2")
    custom_api_key = Column(String(255), nullable=True)

    user = relationship("User", back_populates="settings")
