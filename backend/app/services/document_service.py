import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Document, DocumentChunk, User
from app.rag.parser import DocumentParser
from app.rag.chunker import TextChunker
from app.rag.vector_store import vector_store

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}

class DocumentService:
    """Manages document upload, parsing, chunking, indexing and lifecycle."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def upload_and_process_document(
        self,
        file: UploadFile,
        user: User,
        db: Session,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Document:
        filename = file.filename or "uploaded_file.txt"
        file_ext = Path(filename).suffix.lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Create Document record
        doc = Document(
            user_id=user.id,
            filename=filename,
            file_type=file_ext.lstrip("."),
            file_path="",
            file_size=0,
            status="PROCESSING",
            chunk_count=0
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        dest_filename = f"{doc.id}_{filename}"
        dest_path = self.upload_dir / dest_filename

        try:
            # Save uploaded file
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = dest_path.stat().st_size
            if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                dest_path.unlink(missing_ok=True)
                doc.status = "FAILED"
                doc.error_message = f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                )

            doc.file_path = str(dest_path)
            doc.file_size = file_size
            db.commit()

            # Process Document: Extract, Chunk, Index
            self._process_document(doc, db, chunk_size, chunk_overlap)
            return doc

        except HTTPException:
            raise
        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {str(e)}"
            )

    def _process_document(
        self,
        doc: Document,
        db: Session,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        doc.status = "PROCESSING"
        doc.error_message = None
        db.commit()

        c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

        # 1. Parse pages
        pages = DocumentParser.parse_file(doc.file_path)
        if not pages:
            raise ValueError("No extractable text found in document.")

        # 2. Chunk text
        chunker = TextChunker(chunk_size=c_size, chunk_overlap=c_overlap)
        chunks_data = chunker.chunk_pages(pages, document_id=doc.id, filename=doc.filename)

        if not chunks_data:
            raise ValueError("Chunking produced zero valid chunks.")

        # 3. Clean old chunks in db if reprocessing
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        # 4. Insert chunks into DB
        db_chunks = []
        for ch in chunks_data:
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=ch["chunk_index"],
                page_number=ch["page_number"],
                content=ch["content"]
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)

        db.commit()

        # 5. Index in Vector Store
        vector_store.add_chunks(doc.id, chunks_data)

        # 6. Update document status
        doc.status = "INDEXED"
        doc.chunk_count = len(chunks_data)
        db.commit()
        db.refresh(doc)

    def reprocess_document(self, doc_id: str, user: User, db: Session) -> Document:
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user.id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        if not Path(doc.file_path).exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source file missing from disk.")

        self._process_document(doc, db)
        return doc

    def delete_document(self, doc_id: str, user: User, db: Session):
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user.id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Remove from vector store
        vector_store.delete_document(doc.id)

        # Remove file from disk
        if doc.file_path and Path(doc.file_path).exists():
            try:
                Path(doc.file_path).unlink(missing_ok=True)
            except Exception as e:
                print(f"Error removing file from disk: {e}")

        # Remove from DB (cascade deletes chunks)
        db.delete(doc)
        db.commit()

    def get_user_documents(self, user: User, db: Session) -> List[Document]:
        return db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()

    def get_document_detail(self, doc_id: str, user: User, db: Session) -> Document:
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user.id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        return doc

document_service = DocumentService()
