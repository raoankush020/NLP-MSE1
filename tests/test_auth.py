import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_register_and_login():
    unique_email = f"testuser_{os.urandom(4).hex()}@example.com"
    register_payload = {
        "name": "Dr. Test User",
        "email": unique_email,
        "password": "SecretPassword123!"
    }
    
    # 1. Register
    reg_resp = client.post("/api/auth/register", json=register_payload)
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email

    # 2. Duplicate Register
    dup_resp = client.post("/api/auth/register", json=register_payload)
    assert dup_resp.status_code == 400

    # 3. Login
    login_resp = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "SecretPassword123!"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # 4. Get Current User (/me)
    token = login_data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email
