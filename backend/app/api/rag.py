from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.models import User, QueryRecord, Evaluation
from app.schemas.schemas import QueryRequest, QueryResponse, RetrievedContextItem, ClaimEvaluationItem, HallucinationSummary
from app.api.deps import get_current_user
from app.services.rag_service import rag_service

router = APIRouter(tags=["RAG Query"])

@router.post("/query", response_model=QueryResponse)
def query_rag(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return rag_service.execute_query(request, current_user, db)

@router.get("/query/{id}", response_model=QueryResponse)
def get_query(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query_rec = db.query(QueryRecord).filter(QueryRecord.id == id, QueryRecord.user_id == current_user.id).first()
    if not query_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query record not found.")

    eval_rec = query_rec.evaluation
    retrieved_items = [
        RetrievedContextItem(
            source=rc.source,
            page=rc.page,
            chunk_id=rc.chunk_id,
            similarity=rc.similarity,
            text=rc.text,
            document_id=rc.document_id
        ) for rc in query_rec.retrieved_chunks
    ]

    claims_items = []
    if eval_rec:
        claims_items = [
            ClaimEvaluationItem(
                claim=c.claim_text,
                classification=c.classification,
                score=c.score,
                evidence=c.evidence,
                conflicting_text=c.conflicting_text
            ) for c in eval_rec.claims
        ]
        hallucination_data = HallucinationSummary(
            hallucinated=eval_rec.hallucinated,
            support_score=eval_rec.support_score,
            hallucination_score=eval_rec.hallucination_score,
            classification=eval_rec.classification
        )
    else:
        hallucination_data = HallucinationSummary(
            hallucinated=False,
            support_score=1.0,
            hallucination_score=0.0,
            classification="NOT_HALLUCINATED"
        )

    return QueryResponse(
        query_id=query_rec.id,
        evaluation_id=eval_rec.id if eval_rec else None,
        question=query_rec.question,
        answer=query_rec.answer,
        retrieved_context=retrieved_items,
        hallucination=hallucination_data,
        claims=claims_items,
        created_at=query_rec.created_at
    )
