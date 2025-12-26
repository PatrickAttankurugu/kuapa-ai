import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "2.0.0"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "openai_configured" in data

def test_chat_endpoint_valid_request():
    response = client.post(
        "/chat",
        json={"message": "What are symptoms of nitrogen deficiency in maize?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "request_id" in data
    assert "timings_ms" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0

def test_chat_endpoint_empty_message():
    response = client.post(
        "/chat",
        json={"message": ""}
    )
    assert response.status_code == 200

def test_chat_endpoint_invalid_payload():
    response = client.post("/chat", json={})
    assert response.status_code == 422

def test_chat_endpoint_known_question():
    response = client.post(
        "/chat",
        json={"message": "What are symptoms of nitrogen deficiency in maize?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["response"]) > 0
    assert isinstance(data["response"], str)

def test_audio_endpoint_missing_file():
    response = client.get("/audio/nonexistent.mp3")
    assert response.status_code == 404
