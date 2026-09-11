import pytest
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token():
    unique_email = f"docuser_{os.urandom(4).hex()}@example.com"
    reg_resp = client.post("/api/auth/register", json={
        "name": "Doc Tester",
        "email": unique_email,
        "password": "Password123!"
    })
    return reg_resp.json()["access_token"]

def test_document_upload_and_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    sample_content = (
        "Artificial Intelligence in Healthcare:\n\n"
        "AI algorithms are increasingly being used to analyze complex medical data. "
        "Deep learning models have demonstrated diagnostic accuracy comparable to medical specialists "
        "in identifying diabetic retinopathy, skin cancers, and breast imaging anomalies. "
        "However, clinical integration requires rigorous prospective validation and human-in-the-loop oversight."
    )

    file_bytes = io.BytesIO(sample_content.encode("utf-8"))
    files = {"file": ("healthcare_ai.txt", file_bytes, "text/plain")}

    # 1. Upload
    upload_resp = client.post("/api/documents/upload", headers=headers, files=files)
    assert upload_resp.status_code == 200
    doc_data = upload_resp.json()
    assert doc_data["filename"] == "healthcare_ai.txt"
    assert doc_data["status"] == "INDEXED"
    assert doc_data["chunk_count"] > 0
    doc_id = doc_data["id"]

    # 2. List documents
    list_resp = client.get("/api/documents", headers=headers)
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Document details & chunks
    detail_resp = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["chunks"]) > 0

    # 4. Reprocess document
    reprocess_resp = client.post(f"/api/documents/{doc_id}/reprocess", headers=headers)
    assert reprocess_resp.status_code == 200
    assert reprocess_resp.json()["status"] == "INDEXED"

    # 5. Delete document
    del_resp = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify deleted
    verify_resp = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert verify_resp.status_code == 404
