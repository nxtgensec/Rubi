from app.main import app
from fastapi.testclient import TestClient


def test_inbound_call_returns_answer_instructions() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/telephony/inbound",
        json={
            "provider": "generic",
            "provider_call_id": "provider_123",
            "from_number": "+919000000001",
            "to_number": "+914000000001",
            "agent_id": "agent_demo",
            "preferred_language": "te-IN",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["action"] == "answer"
    assert body["recording_enabled"] is True
    assert body["language"] == "te-IN"


def test_transcript_language_detection_updates_session() -> None:
    client = TestClient(app)
    inbound = client.post(
        "/api/v1/telephony/inbound",
        json={
            "provider": "generic",
            "provider_call_id": "provider_456",
            "from_number": "+919000000002",
            "to_number": "+914000000001",
        },
    ).json()

    response = client.post(
        f"/api/v1/telephony/calls/{inbound['call_id']}/transcript",
        json={"role": "user", "text": "నమస్కారం appointment kavali"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "te-IN"
    assert body["transcript"][0]["language"] == "te-IN"
