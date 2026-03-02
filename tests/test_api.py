import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint_structure():
    """Test if the /chat endpoint accepts the correct payload structure."""
    payload = {
        "session_id": "test_session_123",
        "message": "Qual é a política de bagagem?"
    }
    
    # Since we don't have real API keys in the test environment, we expect a 500
    # due to OpenAI/Tavily errors, BUT the endpoint should be reachable.
    headers = {"X-API-Key": "blis_secret_token_123"}
    response = client.post("/chat", json=payload, headers=headers)
    
    # It shouldn't be a 404 or 422 (validation error)
    assert response.status_code not in [404, 422]

def test_chat_endpoint_streaming():
    """Test if the /chat endpoint correctly handles the stream=True payload."""
    payload = {
        "session_id": "test_session_stream",
        "message": "Qual é a política de bagagem?",
        "stream": True
    }
    
    headers = {"X-API-Key": "blis_secret_token_123"}
    # Using 'with client.stream' allows checking the StreamingResponse headers
    with client.stream("POST", "/chat", json=payload, headers=headers) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

def test_health_check_implied():
    """Test that the app can handle unknown routes properly."""
    response = client.get("/unknown")
    assert response.status_code == 404
