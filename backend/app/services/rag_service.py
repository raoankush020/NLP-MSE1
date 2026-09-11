from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import (
    User,
    QueryRecord,
    RetrievedChunk,
    Evaluation,
    Claim,
    UserSetting
)
from app.schemas.schemas import (
    QueryRequest,
    QueryResponse,
    RetrievedContextItem,
    ClaimEvaluationItem,
    HallucinationSummary,
    EvaluateDirectRequest
)
from app.rag.vector_store import vector_store
from app.rag.generator import generator
from app.hallucination.claim_extractor import claim_extractor
from app.hallucination.verifier import claim_verifier
from app.hallucination.scorer import hallucination_scorer
from app.core.config import settings

class RAGService:
    """Executes end-to-end RAG question answering and factual hallucination verification."""

    def execute_query(
        self,
        request: QueryRequest,
        user: User,
        db: Session
    ) -> QueryResponse:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

        # Fetch user settings if configured
        user_settings = db.query(UserSetting).filter(UserSetting.user_id == user.id).first()
        top_k = request.top_k or (user_settings.top_k if user_settings else settings.DEFAULT_TOP_K)
        temperature = request.temperature or (user_settings.temperature if user_settings else settings.DEFAULT_TEMPERATURE)
        llm_provider = user_settings.llm_model if user_settings else settings.LLM_PROVIDER
        custom_key = user_settings.custom_api_key if user_settings else None

        # 1. Retrieve top-K relevant chunks
        retrieved_raw = vector_store.search(
            query=question,
            top_k=top_k,
            document_ids=request.document_ids
        )

        # 2. Generate answer
        answer = generator.generate_answer(
            question=question,
            retrieved_chunks=retrieved_raw,
            provider=llm_provider,
            custom_key=custom_key,
            temperature=temperature
        )

        # 3. Extract atomic claims from answer
        claims_list = claim_extractor.extract_claims(answer)

        # 4. Verify claims strictly against retrieved context
        evaluated_claims = claim_verifier.verify_claims(claims_list, retrieved_raw)

        # 5. Calculate scores & hallucination classification
        scores_data = hallucination_scorer.calculate_scores(evaluated_claims)

        # 6. Save records into database
        query_record = QueryRecord(
            user_id=user.id,
            question=question,
            answer=answer
        )
        db.add(query_record)
        db.commit()
        db.refresh(query_record)

        # Save retrieved chunks
        retrieved_context_items: List[RetrievedContextItem] = []
        for ch in retrieved_raw:
            chunk_rec = RetrievedChunk(
                query_id=query_record.id,
                document_id=ch.get("document_id"),
                chunk_id=str(ch.get("chunk_index", "")),
                source=ch.get("filename", "Doc"),
                page=ch.get("page_number", 1),
                similarity=ch.get("similarity", 0.0),
                text=ch.get("content", "")
            )
            db.add(chunk_rec)
            retrieved_context_items.append(
                RetrievedContextItem(
                    source=chunk_rec.source,
                    page=chunk_rec.page,
                    chunk_id=chunk_rec.chunk_id,
                    similarity=chunk_rec.similarity,
                    text=chunk_rec.text,
                    document_id=chunk_rec.document_id
                )
            )

        # Save Evaluation
        evaluation_rec = Evaluation(
            query_id=query_record.id,
            user_id=user.id,
            support_score=scores_data["support_score"],
            hallucination_score=scores_data["hallucination_score"],
            classification=scores_data["classification"],
            hallucinated=scores_data["hallucinated"]
        )
        db.add(evaluation_rec)
        db.commit()
        db.refresh(evaluation_rec)

        # Save Claims
        claims_items: List[ClaimEvaluationItem] = []
        for idx, ec in enumerate(evaluated_claims):
            claim_rec = Claim(
                evaluation_id=evaluation_rec.id,
                claim_text=ec["claim"],
                classification=ec["classification"],
                score=ec["score"],
                evidence=ec.get("evidence"),
                conflicting_text=ec.get("conflicting_text"),
                order_index=idx
            )
            db.add(claim_rec)
            claims_items.append(
                ClaimEvaluationItem(
                    claim=ec["claim"],
                    classification=ec["classification"],
                    score=ec["score"],
                    evidence=ec.get("evidence"),
                    conflicting_text=ec.get("conflicting_text")
                )
            )

        db.commit()

        return QueryResponse(
            query_id=query_record.id,
            evaluation_id=evaluation_rec.id,
            question=question,
            answer=answer,
            retrieved_context=retrieved_context_items,
            hallucination=HallucinationSummary(
                hallucinated=scores_data["hallucinated"],
                support_score=scores_data["support_score"],
                hallucination_score=scores_data["hallucination_score"],
                classification=scores_data["classification"]
            ),
            claims=claims_items,
            created_at=query_record.created_at
        )

    def evaluate_direct_text(
        self,
        request: EvaluateDirectRequest,
        user: User,
        db: Session
    ) -> QueryResponse:
        """Evaluates arbitrary question, answer, and provided context text directly."""
        context_chunk = [{
            "content": request.context,
            "filename": "DirectInput",
            "page_number": 1,
            "similarity": 1.0,
            "chunk_index": 0
        }]

        claims_list = claim_extractor.extract_claims(request.answer)
        evaluated_claims = claim_verifier.verify_claims(claims_list, context_chunk)
        scores_data = hallucination_scorer.calculate_scores(evaluated_claims)

        query_record = QueryRecord(
            user_id=user.id,
            question=request.question,
            answer=request.answer
        )
        db.add(query_record)
        db.commit()
        db.refresh(query_record)

        chunk_rec = RetrievedChunk(
            query_id=query_record.id,
            source="DirectInput",
            page=1,
            similarity=1.0,
            text=request.context
        )
        db.add(chunk_rec)

        evaluation_rec = Evaluation(
            query_id=query_record.id,
            user_id=user.id,
            support_score=scores_data["support_score"],
            hallucination_score=scores_data["hallucination_score"],
            classification=scores_data["classification"],
            hallucinated=scores_data["hallucinated"]
        )
        db.add(evaluation_rec)
        db.commit()
        db.refresh(evaluation_rec)

        claims_items = []
        for idx, ec in enumerate(evaluated_claims):
            c_rec = Claim(
                evaluation_id=evaluation_rec.id,
                claim_text=ec["claim"],
                classification=ec["classification"],
                score=ec["score"],
                evidence=ec.get("evidence"),
                conflicting_text=ec.get("conflicting_text"),
                order_index=idx
            )
            db.add(c_rec)
            claims_items.append(ClaimEvaluationItem(
                claim=ec["claim"],
                classification=ec["classification"],
                score=ec["score"],
                evidence=ec.get("evidence"),
                conflicting_text=ec.get("conflicting_text")
            ))

        db.commit()

        return QueryResponse(
            query_id=query_record.id,
            evaluation_id=evaluation_rec.id,
            question=request.question,
            answer=request.answer,
            retrieved_context=[RetrievedContextItem(
                source="DirectInput",
                page=1,
                chunk_id=0,
                similarity=1.0,
                text=request.context
            )],
            hallucination=HallucinationSummary(
                hallucinated=scores_data["hallucinated"],
                support_score=scores_data["support_score"],
                hallucination_score=scores_data["hallucination_score"],
                classification=scores_data["classification"]
            ),
            claims=claims_items,
            created_at=query_record.created_at
        )

rag_service = RAGService()
