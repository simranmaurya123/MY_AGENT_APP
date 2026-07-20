import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from api import app

# Pytest fixture that ensures FastAPI lifespan events run
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    """Verify that the health check endpoint returns 200 and correct status keys."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "classifier" in data
    assert "retriever" in data
    assert "openai_enabled" in data

def test_classify_endpoint_valid(client):
    """Test classification of a valid AI/ML query."""
    payload = {"query": "What is reinforcement learning and Q-learning?"}
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["domain"] in ["RL", "ML", "AI", "DL", "CV", "NLP"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["backend"] in ["distilbert", "llm"]

def test_classify_endpoint_invalid(client):
    """Test classification of an empty query."""
    payload = {"query": ""}
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "UNKNOWN"

def test_chat_routing_rejection(client):
    """Test that a query outside the supported domains is rejected."""
    payload = {"query": "What is the capital of France and how do I bake a cake?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "I only answer questions in AI, ML, DL, NLP, RL, and CV" in data["answer"]
    assert data["domain"] == "UNKNOWN"

def test_upload_invalid_type(client):
    """Test that non-PDF file uploads are rejected with 400 Bad Request."""
    files = {"file": ("test.txt", b"dummy content", "text/plain")}
    data = {"domain": "AI"}
    response = client.post("/upload", files=files, data=data)
    assert response.status_code == 400
    assert "Only PDF file uploads are supported" in response.json()["detail"]

def test_upload_invalid_domain(client):
    """Test that uploading to an unsupported domain is rejected."""
    files = {"file": ("test.pdf", b"dummy pdf content", "application/pdf")}
    data = {"domain": "POLITICS"}
    response = client.post("/upload", files=files, data=data)
    assert response.status_code == 400
    assert "Unsupported domain" in response.json()["detail"]
