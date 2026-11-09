"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "Fresno Carrier Finder" in res.text
    assert "Business Discovery" in res.text


def test_get_settings():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "google" in data
    assert "twilio" in data
    assert "defaults" in data


def test_update_settings():
    res = client.post(
        "/api/settings",
        json={
            "google_places_api_key": "AIza_mock_test_key_sample",
            "twilio_account_sid": "AC_mock_account_sid_sample",
            "twilio_api_key_sid": "SK_mock_key_sid_sample",
            "twilio_api_secret": "mock_secret_test_value",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Check that masked response does not leak raw secrets
    settings = data["settings"]
    assert "mock_secret_test_value" not in str(settings)


def test_scan_lifecycle_and_export():
    # 1. Start demo scan
    start_res = client.post(
        "/api/scan/start",
        json={
            "categories": ["restaurant", "dentist"],
            "max_businesses": 10,
            "max_lookups": 5,
            "provider_mode": "demo",
        },
    )
    assert start_res.status_code in {200, 409}

    # 2. Poll progress
    prog_res = client.get("/api/scan/progress")
    assert prog_res.status_code == 200

    # 3. Get results
    results_res = client.get("/api/scan/results?match_status=all")
    assert results_res.status_code == 200
    results_data = results_res.json()
    assert "records" in results_data

    # 4. Export CSV
    export_res = client.post("/api/export/csv", json={"filter_mode": "confirmed_only"})
    assert export_res.status_code in {200, 400}  # 400 only if 0 records yet
    if export_res.status_code == 200:
        assert export_res.headers["content-type"].startswith("text/csv")
        assert export_res.content.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
