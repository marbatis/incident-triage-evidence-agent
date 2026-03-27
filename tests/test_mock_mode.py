from __future__ import annotations


def test_health_reports_mock_mode_without_key(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["active_provider"] == "mock"


def test_mock_provider_memo_present(client) -> None:
    response = client.post("/api/triage/sample/cert_expiry_auth_service")
    assert response.status_code == 201
    payload = response.json()
    assert "Incident" in payload["memo"]
    assert payload["incident_id"].startswith("INC-")
