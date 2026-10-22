
"""
Tests for Component C's readable demonstration API.

No Gemini API calls are made.
"""

import pytest

from fastapi.testclient import TestClient

from api.main import app
from api import recorded_demo


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_readable_endpoint_success(client):
    """
    The readable endpoint should return text
    containing the existing recorded reasoning.
    """

    response = client.get(
        "/api/reasoning/demo/readable"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("text/plain")

    report = response.text

    assert "DEMONSTRATION MODE: RECORDED" in report

    assert "LEGAL ISSUE" in report
    assert "AUTHORITIES CONSIDERED" in report
    assert "CROSS-CASE ANALYSIS" in report
    assert "CONCLUSION" in report


def test_readable_endpoint_preserves_evidence(client):
    """
    Existing case IDs and passage references
    should appear in the formatted report.
    """

    response = client.get(
        "/api/reasoning/demo/readable"
    )

    assert response.status_code == 200

    report = response.text

    assert "MOCK_SC_001:P1" in report
    assert "MOCK_CA_002:P2" in report
    assert "MOCK_SC_003:P3" in report

    assert "no_longer_good_law" in report


def test_readable_endpoint_labels_recorded_output(client):
    """
    The API must not imply that this is a fresh
    Gemini-generated result.
    """

    response = client.get(
        "/api/reasoning/demo/readable"
    )

    assert response.status_code == 200

    assert "DEMONSTRATION MODE: RECORDED" in response.text

    assert "not a live Gemini result" in response.text

    assert "Not available in this response." in response.text


def test_readable_endpoint_handles_missing_file(
    client,
    monkeypatch,
    tmp_path
):
    """
    If the recorded fixture is missing,
    the endpoint should return 404.
    """

    missing_file = (
        tmp_path / "missing_response.json"
    )

    monkeypatch.setattr(
        recorded_demo,
        "RECORDED_RESULT_FILE",
        missing_file
    )

    response = client.get(
        "/api/reasoning/demo/readable"
    )

    assert response.status_code == 404

    assert "not found" in (
        response.json()["detail"].lower()
    )
