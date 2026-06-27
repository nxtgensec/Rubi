from app.main import app
from fastapi.testclient import TestClient


def test_twilio_voice_webhook_returns_twiml() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/twilio/voice",
        data={
            "CallSid": "CA123",
            "From": "+919000000001",
            "To": "+14244963973",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Response>" in response.text
    assert "<Gather" in response.text
    assert "nenu Rubi nundi maatladutunna" in response.text
    assert "budget range cheppandi" in response.text


def test_twilio_gather_stores_readable_lead_details() -> None:
    client = TestClient(app)
    inbound = client.post(
        "/api/v1/twilio/voice",
        data={
            "CallSid": "CA789",
            "From": "+919000000003",
            "To": "+14244963973",
        },
    )
    call_id = inbound.text.split("call_id=")[1].split('"')[0]

    response = client.post(
        f"/api/v1/twilio/gather?call_id={call_id}",
        data={
            "SpeechResult": "My name is Ravi. I need a website and my budget is 50000. yes proceed",
        },
    )

    calls = client.get("/api/v1/calls").json()
    stored = next(call for call in calls if call["id"] == call_id)
    assert response.status_code == 200
    assert stored["sentiment"] == "agreed"
    assert "Budget" in stored["summary"]


def test_twilio_recording_callback_accepts_form() -> None:
    client = TestClient(app)
    inbound = client.post(
        "/api/v1/telephony/inbound",
        json={
            "provider": "twilio",
            "provider_call_id": "CA456",
            "from_number": "+919000000002",
            "to_number": "+14244963973",
        },
    ).json()

    response = client.post(
        f"/api/v1/twilio/recording?call_id={inbound['call_id']}",
        data={
            "RecordingSid": "RE123",
            "RecordingUrl": "https://api.twilio.com/recording.wav",
            "RecordingStatus": "completed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
