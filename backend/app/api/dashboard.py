from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.models import User, Document, QueryRecord, Evaluation, Claim
from app.schemas.schemas import DashboardStatsResponse, DashboardChartsResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
    total_queries = db.query(QueryRecord).filter(QueryRecord.user_id == current_user.id).count()
    
    evals = db.query(Evaluation).filter(Evaluation.user_id == current_user.id).all()
    total_evals = len(evals)

    grounded_count = sum(1 for e in evals if not e.hallucinated)
    hallucinated_count = sum(1 for e in evals if e.hallucinated)

    if total_evals > 0:
        avg_support = sum(e.support_score for e in evals) / total_evals
        avg_hallucination = sum(e.hallucination_score for e in evals) / total_evals
    else:
        avg_support = 0.0
        avg_hallucination = 0.0

    return DashboardStatsResponse(
        total_documents=total_docs,
        total_queries=total_queries,
        total_evaluations=total_evals,
        grounded_answers=grounded_count,
        hallucinated_answers=hallucinated_count,
        average_hallucination_score=round(avg_hallucination, 4),
        average_support_score=round(avg_support, 4)
    )

@router.get("/charts", response_model=DashboardChartsResponse)
def get_dashboard_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evals = db.query(Evaluation).filter(Evaluation.user_id == current_user.id).all()
    queries = db.query(QueryRecord).filter(QueryRecord.user_id == current_user.id).all()

    # 1. Grounded vs Hallucinated
    grounded = sum(1 for e in evals if not e.hallucinated)
    hallucinated = sum(1 for e in evals if e.hallucinated)
    grounded_vs_hallucinated = [
        {"name": "Grounded", "value": grounded, "color": "#10b981"},
        {"name": "Hallucinated", "value": hallucinated, "color": "#ef4444"}
    ]

    # 2. Hallucination Types / Severity
    type_counts = {
        "NOT_HALLUCINATED": 0,
        "LOW_HALLUCINATION": 0,
        "MEDIUM_HALLUCINATION": 0,
        "HIGH_HALLUCINATION": 0
    }
    for e in evals:
        if e.classification in type_counts:
            type_counts[e.classification] += 1
    hallucination_types = [
        {"name": "Not Hallucinated", "value": type_counts["NOT_HALLUCINATED"], "color": "#10b981"},
        {"name": "Low Hallucination", "value": type_counts["LOW_HALLUCINATION"], "color": "#3b82f6"},
        {"name": "Medium Hallucination", "value": type_counts["MEDIUM_HALLUCINATION"], "color": "#f59e0b"},
        {"name": "High Hallucination", "value": type_counts["HIGH_HALLUCINATION"], "color": "#ef4444"},
    ]

    # 3. Queries over time (group by last 7 days or date)
    days_map: Dict[str, int] = {}
    now = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        day_str = (now - timedelta(days=i)).strftime("%b %d")
        days_map[day_str] = 0

    for q in queries:
        if q.created_at:
            day_str = q.created_at.strftime("%b %d")
            if day_str in days_map:
                days_map[day_str] += 1

    queries_over_time = [{"name": day, "queries": count} for day, count in days_map.items()]

    # 4. Support score distribution bins (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
    bins = {"0-20%": 0, "21-40%": 0, "41-60%": 0, "61-80%": 0, "81-100%": 0}
    for e in evals:
        pct = e.support_score * 100
        if pct <= 20:
            bins["0-20%"] += 1
        elif pct <= 40:
            bins["21-40%"] += 1
        elif pct <= 60:
            bins["41-60%"] += 1
        elif pct <= 80:
            bins["61-80%"] += 1
        else:
            bins["81-100%"] += 1

    support_score_distribution = [{"range": k, "count": v} for k, v in bins.items()]

    # 5. Hallucination rate progression
    hallucination_rates = []
    accum_evals = 0
    accum_hallucinated = 0
    sorted_evals = sorted(evals, key=lambda x: x.created_at or datetime.min)
    for idx, e in enumerate(sorted_evals):
        accum_evals += 1
        if e.hallucinated:
            accum_hallucinated += 1
        rate = round((accum_hallucinated / accum_evals) * 100, 1)
        label = e.created_at.strftime("%m/%d %H:%M") if e.created_at else f"#{idx+1}"
        hallucination_rates.append({"name": label, "rate": rate})

    if not hallucination_rates:
        hallucination_rates = [{"name": "No Data", "rate": 0}]

    # 6. Claim Classifications across all user's evaluations
    eval_ids = [e.id for e in evals]
    claims = db.query(Claim).filter(Claim.evaluation_id.in_(eval_ids)).all() if eval_ids else []
    claim_counts = {"SUPPORTED": 0, "PARTIALLY_SUPPORTED": 0, "UNSUPPORTED": 0, "CONTRADICTED": 0}
    for c in claims:
        if c.classification in claim_counts:
            claim_counts[c.classification] += 1

    claim_classifications = [
        {"name": "Supported", "value": claim_counts["SUPPORTED"], "color": "#10b981"},
        {"name": "Partially Supported", "value": claim_counts["PARTIALLY_SUPPORTED"], "color": "#f59e0b"},
        {"name": "Unsupported", "value": claim_counts["UNSUPPORTED"], "color": "#ef4444"},
        {"name": "Contradicted", "value": claim_counts["CONTRADICTED"], "color": "#8b5cf6"},
    ]

    return DashboardChartsResponse(
        grounded_vs_hallucinated=grounded_vs_hallucinated,
        hallucination_rates=hallucination_rates,
        queries_over_time=queries_over_time,
        support_score_distribution=support_score_distribution,
        hallucination_types=hallucination_types,
        claim_classifications=claim_classifications
    )
