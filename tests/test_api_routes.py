from __future__ import annotations

from pathlib import Path


def test_home_page_renders(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Read-Only Incident Triage" in response.text


def test_sample_triage_route_and_detail_fetch(client) -> None:
    sample_response = client.post("/api/triage/sample/retry_storm_payments")
    assert sample_response.status_code == 201

    result = sample_response.json()
    triage_id = result["triage_id"]

    detail_response = client.get(f"/api/triage/{triage_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()

    assert detail["incident_id"] == "INC-2026-1002"
    assert detail["scenario_type"] == "retry_storm"
    assert detail["severity"] == "SEV2"


def test_upload_triage_route(client) -> None:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "upload_incident.json"
    with fixture_path.open("rb") as handle:
        response = client.post(
            "/api/triage/upload",
            files={"file": ("upload_incident.json", handle, "application/json")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["incident_id"] == "INC-2026-1004"
    assert payload["scenario_type"] == "dependency_outage"


def test_history_page_lists_triage_entries(client) -> None:
    post_response = client.post("/api/triage/sample/cert_expiry_auth_service")
    assert post_response.status_code == 201
    triage_id = post_response.json()["triage_id"]

    history_response = client.get("/history")
    assert history_response.status_code == 200
    assert triage_id in history_response.text
