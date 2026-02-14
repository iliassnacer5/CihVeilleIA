"""
Tests minimums pour vérifier le bon fonctionnement de l'API.

Usage:
    python -m pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.backend.api import app


@pytest.fixture
def client():
    """Crée un client de test pour l'API."""
    return TestClient(app)


# --- Test 1: Healthcheck ---

def test_healthcheck(client):
    """Vérifie que le endpoint /health répond correctement."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


# --- Test 2: Authentication Flow ---

def test_login_invalid_credentials(client):
    """Vérifie que les credentials incorrects retournent 401."""
    response = client.post("/token", data={
        "username": "nonexistent_user_xyz",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_protected_endpoint_without_token(client):
    """Vérifie que les endpoints protégés refusent l'accès sans token."""
    response = client.get("/documents")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token(client):
    """Vérifie que les endpoints protégés refusent un token invalide."""
    response = client.get(
        "/documents",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


# --- Test 3: API Routes Exist ---

def test_sources_endpoint_requires_auth(client):
    """Vérifie que le endpoint /sources existe et nécessite auth."""
    response = client.get("/sources")
    assert response.status_code == 401


def test_search_endpoint_requires_auth(client):
    """Vérifie que le endpoint /search existe et nécessite auth."""
    response = client.post("/search", json={"question": "test"})
    assert response.status_code == 401


def test_chatbot_endpoint_requires_auth(client):
    """Vérifie que le endpoint /chatbot/ask existe et nécessite auth."""
    response = client.post("/chatbot/ask", json={"question": "test"})
    assert response.status_code == 401


def test_kpis_endpoint_requires_auth(client):
    """Vérifie que le endpoint /analytics/kpis existe et nécessite auth."""
    response = client.get("/analytics/kpis")
    assert response.status_code == 401
