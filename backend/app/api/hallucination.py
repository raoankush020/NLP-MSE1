from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.models import User, Evaluation, QueryRecord, Claim, RetrievedChunk
from app.schemas.schemas import (
    EvaluateDirectRequest,
    EvaluationListItem,
    EvaluationDetailResponse,
    QueryResponse,
    RetrievedContextItem,
    ClaimEvaluationItem
)
from app.api.deps import get_current_user
from app.services.rag_service import rag_service

router = APIRouter(tags=["Hallucination Evaluation"])

@router.post("/evaluate", response_model=QueryResponse)
def evaluate_direct(
    request: EvaluateDirectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return rag_service.evaluate_direct_text(request, current_user, db)

@router.get("/evaluations", response_model=List[EvaluationListItem])
def list_evaluations(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Evaluation).join(QueryRecord).filter(Evaluation.user_id == current_user.id)

    if search:
        query = query.filter(QueryRecord.question.ilike(f"%{search}%"))

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Evaluation.classification == status_filter.upper())

    evaluations = query.order_by(desc(Evaluation.created_at)).offset(offset).limit(limit).all()

    items = []
    for ev in evaluations:
        items.append(EvaluationListItem(
            id=ev.id,
            query_id=ev.query_id,
            question=ev.query.question if ev.query else "",
            support_score=ev.support_score,
            hallucination_score=ev.hallucination_score,
            classification=ev.classification,
            hallucinated=ev.hallucinated,
            created_at=ev.created_at
        ))
    return items

@router.get("/evaluations/{id}", response_model=EvaluationDetailResponse)
def get_evaluation_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ev = db.query(Evaluation).filter(Evaluation.id == id, Evaluation.user_id == current_user.id).first()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation record not found.")

    query_rec = ev.query
    retrieved_chunks = db.query(RetrievedChunk).filter(RetrievedChunk.query_id == ev.query_id).all()
    claims = db.query(Claim).filter(Claim.evaluation_id == ev.id).order_by(Claim.order_index.asc()).all()

    context_items = [
        RetrievedContextItem(
            source=rc.source,
            page=rc.page,
            chunk_id=rc.chunk_id,
            similarity=rc.similarity,
            text=rc.text,
            document_id=rc.document_id
        ) for rc in retrieved_chunks
    ]

    claim_items = [
        ClaimEvaluationItem(
            claim=c.claim_text,
            classification=c.classification,
            score=c.score,
            evidence=c.evidence,
            conflicting_text=c.conflicting_text
        ) for c in claims
    ]

    return EvaluationDetailResponse(
        id=ev.id,
        query_id=ev.query_id,
        question=query_rec.question if query_rec else "",
        answer=query_rec.answer if query_rec else "",
        support_score=ev.support_score,
        hallucination_score=ev.hallucination_score,
        classification=ev.classification,
        hallucinated=ev.hallucinated,
        created_at=ev.created_at,
        retrieved_context=context_items,
        claims=claim_items
    )
