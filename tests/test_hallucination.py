import pytest
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.hallucination.claim_extractor import claim_extractor
from app.hallucination.verifier import claim_verifier
from app.hallucination.scorer import hallucination_scorer

client = TestClient(app)

def test_claim_extraction():
    answer = "Python was created by Guido van Rossum in 1991. Python is widely used for machine learning."
    claims = claim_extractor.extract_claims(answer)
    assert len(claims) >= 2
    assert any("Guido van Rossum" in c for c in claims)
    assert any("1991" in c for c in claims)

def test_claim_verification_and_scoring():
    retrieved_chunks = [{
        "content": "Python was created by Guido van Rossum in 1991 as a successor to the ABC language.",
        "filename": "python_history.txt",
        "page_number": 1,
        "similarity": 0.95
    }]

    claims = [
        "Python was created by Guido van Rossum.",
        "Python was created in 1991.",
        "Python was invented by Dennis Ritchie at Bell Labs." # Hallucination
    ]

    verified = claim_verifier.verify_claims(claims, retrieved_chunks)
    assert len(verified) == 3
    assert verified[0]["classification"] == "SUPPORTED"
    assert verified[0]["score"] == 1.0
    assert verified[1]["classification"] == "SUPPORTED"
    assert verified[1]["score"] == 1.0
    assert verified[2]["classification"] in ["UNSUPPORTED", "CONTRADICTED"]
    assert verified[2]["score"] == 0.0

    scores = hallucination_scorer.calculate_scores(verified)
    assert scores["support_score"] == pytest.approx(2.0 / 3.0, 0.01)
    assert scores["hallucination_score"] == pytest.approx(1.0 / 3.0, 0.01)

def test_full_query_pipeline():
    # Register user
    email = f"rag_{os.urandom(4).hex()}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "RAG Explorer",
        "email": email,
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload document
    doc_text = "The James Webb Space Telescope was launched on December 25 2021 from Kourou French Guiana aboard an Ariane 5 rocket."
    files = {"file": ("jwst.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")}
    up_resp = client.post("/api/documents/upload", headers=headers, files=files)
    assert up_resp.status_code == 200

    # Query RAG
    query_payload = {
        "question": "When and where was the James Webb Space Telescope launched?"
    }
    q_resp = client.post("/api/query", headers=headers, json=query_payload)
    assert q_resp.status_code == 200
    q_data = q_resp.json()

    assert "query_id" in q_data
    assert "answer" in q_data
    assert len(q_data["retrieved_context"]) > 0
    assert "hallucination" in q_data
    assert "support_score" in q_data["hallucination"]
    assert "claims" in q_data
    assert len(q_data["claims"]) > 0

    # Check Dashboard Stats API
    dash_resp = client.get("/api/dashboard/stats", headers=headers)
    assert dash_resp.status_code == 200
    stats = dash_resp.json()
    assert stats["total_documents"] >= 1
    assert stats["total_queries"] >= 1
    assert stats["total_evaluations"] >= 1

    # Check Dashboard Charts API
    charts_resp = client.get("/api/dashboard/charts", headers=headers)
    assert charts_resp.status_code == 200
    charts = charts_resp.json()
    assert len(charts["grounded_vs_hallucinated"]) > 0
    assert len(charts["queries_over_time"]) > 0
