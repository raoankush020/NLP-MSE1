from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, Document, DocumentChunk
from app.schemas.schemas import DocumentResponse, DocumentDetailResponse, DocumentChunkResponse
from app.api.deps import get_current_user
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return document_service.upload_and_process_document(
        file=file,
        user=current_user,
        db=db,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return document_service.get_user_documents(current_user, db)

@router.get("/{id}", response_model=DocumentDetailResponse)
def get_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = document_service.get_document_detail(id, current_user, db)
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == id).order_by(DocumentChunk.chunk_index.asc()).all()
    chunk_responses = [DocumentChunkResponse.model_validate(c) for c in chunks]

    return DocumentDetailResponse(
        id=doc.id,
        user_id=doc.user_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=chunk_responses
    )

@router.delete("/{id}")
def delete_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document_service.delete_document(id, current_user, db)
    return {"message": "Document deleted successfully", "id": id}

@router.post("/{id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return document_service.reprocess_document(id, current_user, db)
