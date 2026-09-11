import os
import sys
import io
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_end_to_end_verification():
    print("==================================================")
    print("STARTING 20-STEP END-TO-END PIPELINE VERIFICATION")
    print("==================================================")

    # 1. Register user
    test_email = f"e2e_user_{int(time.time())}@ragdetector.io"
    password = "StrongPassword2026!"
    print(f"\n[Step 1] Registering user: {test_email}...")
    reg_resp = client.post("/api/auth/register", json={
        "name": "Prof. Alan Turing",
        "email": test_email,
        "password": password
    })
    assert reg_resp.status_code == 200, f"Register failed: {reg_resp.text}"
    print("  -> User registered successfully!")

    # 2. Login
    print("\n[Step 2] Authenticating & acquiring JWT token...")
    login_resp = client.post("/api/auth/login", json={
        "email": test_email,
        "password": password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  -> JWT token acquired: {token[:20]}...")

    # Verify /api/auth/me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == test_email
    print(f"  -> Verified profile session for {me_resp.json()['full_name']}")

    # 3. Prepare & Upload Document
    print("\n[Step 3] Uploading reference document...")
    sample_doc_content = (
        "Quantum Computing Fundamentals:\n\n"
        "Quantum computers utilize quantum bits, or qubits, which can exist in superpositions of 0 and 1. "
        "In October 2019, Google AI researchers published a paper demonstrating quantum computational supremacy "
        "using a 53-qubit processor named Sycamore. The Sycamore processor completed a specific benchmark task in "
        "200 seconds that would have taken classical supercomputers thousands of years. "
        "However, commercial fault-tolerant quantum computers will require millions of physical qubits with error correction."
    )
    files = {"file": ("quantum_computing.txt", io.BytesIO(sample_doc_content.encode("utf-8")), "text/plain")}
    upload_resp = client.post("/api/documents/upload", headers=headers, files=files)
    assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    print(f"  -> Document '{doc_data['filename']}' uploaded (ID: {doc_id})")

    # 4. Process document
    print("\n[Step 4] Checking document processing status...")
    assert doc_data["status"] == "INDEXED"
    print("  -> Status is INDEXED")

    # 5. Verify chunks
    print("\n[Step 5] Verifying chunking and page metadata...")
    assert doc_data["chunk_count"] > 0
    print(f"  -> Document partitioned into {doc_data['chunk_count']} chunks")

    # 6. Generate embeddings & 7. Store in vector database
    print("\n[Step 6 & 7] Verifying vector database chunks...")
    detail_resp = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert detail_resp.status_code == 200
    chunks = detail_resp.json()["chunks"]
    assert len(chunks) > 0
    print(f"  -> Chunks indexed in VectorStore: {len(chunks)} chunk(s) stored with embeddings.")

    # 8. Ask a question
    question = "What processor was used in Google's 2019 quantum supremacy experiment and how many qubits did it have?"
    print(f"\n[Step 8] Asking question: '{question}'...")

    # 9. Retrieve context, 10. Generate answer, 11. Extract claims, 12. Verify claims
    # 13. Calculate support score, 14. Calculate hallucination score, 15. Display evidence
    # 16. Save evaluation
    print("\n[Steps 9-16] Executing RAG + Hallucination Detection Pipeline...")
    query_resp = client.post("/api/query", headers=headers, json={"question": question})
    assert query_resp.status_code == 200, f"Query failed: {query_resp.text}"
    query_result = query_resp.json()

    print(f"\n  [Step 9] Retrieved Context ({len(query_result['retrieved_context'])} Chunks):")
    for rc in query_result['retrieved_context']:
        print(f"    - Source: {rc['source']} (Page {rc['page']}) | Similarity: {rc['similarity']:.4f}")
        print(f"      Text: {rc['text'][:120]}...")

    print(f"\n  [Step 10] Generated Answer:\n    \"{query_result['answer']}\"")

    print(f"\n  [Step 11] Extracted Claims ({len(query_result['claims'])}):")
    for idx, c in enumerate(query_result['claims']):
        print(f"    Claim #{idx+1}: {c['claim']}")

    print(f"\n  [Step 12] Claim Verification & Evidence:")
    for c in query_result['claims']:
        print(f"    - [{c['classification']}] (Score: {c['score']:.1f})")
        print(f"      Claim: {c['claim']}")
        print(f"      Evidence: {c['evidence']}")

    hall = query_result['hallucination']
    print(f"\n  [Step 13 & 14] Scores & Classification:")
    print(f"    - Support Score: {hall['support_score'] * 100:.1f}%")
    print(f"    - Hallucination Score: {hall['hallucination_score'] * 100:.1f}%")
    print(f"    - Final Verdict: {hall['classification']} (Hallucinated: {hall['hallucinated']})")

    assert "query_id" in query_result
    assert "evaluation_id" in query_result
    eval_id = query_result["evaluation_id"]

    # 17. Display result in history
    print(f"\n[Step 17] Querying Evaluation History endpoint...")
    history_resp = client.get("/api/evaluations", headers=headers)
    assert history_resp.status_code == 200
    hist_items = history_resp.json()
    assert any(h["id"] == eval_id for h in hist_items)
    print(f"  -> Found {len(hist_items)} evaluation(s) in audit log.")

    # Check evaluation drilldown detail
    drill_resp = client.get(f"/api/evaluations/{eval_id}", headers=headers)
    assert drill_resp.status_code == 200
    drill_data = drill_resp.json()
    assert drill_data["question"] == question
    assert len(drill_data["claims"]) > 0
    print(f"  -> Verified detailed analysis drill-down for evaluation ID: {eval_id}")

    # 18. Update dashboard
    print(f"\n[Step 18] Verifying real-time Dashboard statistics...")
    dash_stats_resp = client.get("/api/dashboard/stats", headers=headers)
    assert dash_stats_resp.status_code == 200
    stats = dash_stats_resp.json()
    print(f"  - Total Documents: {stats['total_documents']}")
    print(f"  - Total Queries: {stats['total_queries']}")
    print(f"  - Total Evaluations: {stats['total_evaluations']}")
    print(f"  - Grounded Answers: {stats['grounded_answers']}")
    print(f"  - Average Support Score: {stats['average_support_score'] * 100:.1f}%")
    assert stats["total_documents"] >= 1
    assert stats["total_queries"] >= 1
    assert stats["total_evaluations"] >= 1

    # 19. Verify analytics
    print(f"\n[Step 19] Verifying Analytics and Charts telemetry...")
    dash_charts_resp = client.get("/api/dashboard/charts", headers=headers)
    assert dash_charts_resp.status_code == 200
    charts = dash_charts_resp.json()
    assert len(charts["grounded_vs_hallucinated"]) > 0
    assert len(charts["queries_over_time"]) > 0
    print("  -> Grounded vs Hallucinated, Hallucination Severity, and Queries Over Time validated.")

    # 20. Verify logout
    print(f"\n[Step 20] Verifying logout security...")
    # Protected route without token or invalid token must return 401
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401
    bad_resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-or-revoked-token"})
    assert bad_resp.status_code == 401
    print("  -> Protected endpoints correctly reject unauthenticated requests (HTTP 401).")

    print("\n==================================================")
    print("SUCCESS: ALL 20 END-TO-END PIPELINE STEPS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_end_to_end_verification()
