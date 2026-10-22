
"""
Tests for the recorded experiment demonstration API.

No Gemini API requests are made.
"""

from fastapi.testclient import TestClient

from api.main import app
from api import experiment_demo


client = TestClient(app)


def test_list_four_experiments():
    response = client.get(
        "/api/reasoning/demo/experiments"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 4

    assert all(item["available"] for item in data)


def test_baseline_experiment_loads():
    response = client.get(
        "/api/reasoning/demo/experiments/"
        "scenario_1_baseline"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "recorded"
    assert data["comparison_available"] is True
    assert len(data["result"]["authorities"]) == 3


def test_treatment_experiment_loads():
    response = client.get(
        "/api/reasoning/demo/experiments/"
        "scenario_2_treatment_changed"
    )

    assert response.status_code == 200

    data = response.json()

    authorities = data["result"]["authorities"]

    case = next(
        item
        for item in authorities
        if item["case_id"] == "MOCK_SC_003"
    )

    assert case["validity_status"] == "good_law"


def test_unknown_scenario_returns_404():
    response = client.get(
        "/api/reasoning/demo/experiments/"
        "unknown_scenario"
    )

    assert response.status_code == 404


def test_missing_experiment_returns_404(
    monkeypatch,
    tmp_path
):
    monkeypatch.setattr(
        experiment_demo,
        "EXPERIMENT_DIR",
        tmp_path
    )

    response = client.get(
        "/api/reasoning/demo/experiments/"
        "scenario_1_baseline"
    )

    assert response.status_code == 404


def test_invalid_experiment_returns_500(
    monkeypatch,
    tmp_path
):
    monkeypatch.setattr(
        experiment_demo,
        "EXPERIMENT_DIR",
        tmp_path
    )

    file_path = (
        tmp_path / "scenario_1_baseline_response.json"
    )

    file_path.write_text(
        '{"invalid": true}',
        encoding="utf-8"
    )

    response = client.get(
        "/api/reasoning/demo/experiments/"
        "scenario_1_baseline"
    )

    assert response.status_code == 500


def test_comparison_reflects_treatment_change():
    response = client.get(
        "/api/reasoning/demo/compare"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "recorded"

    assert data["compared_case_id"] == "MOCK_SC_003"

    assert (
        data["baseline"]["validity_status"]
        == "no_longer_good_law"
    )

    assert (
        data["modified"]["validity_status"]
        == "good_law"
    )

    assert data["baseline"]["authority_assessment"]
    assert data["modified"]["authority_assessment"]

    assert (
        data["baseline"]["conflicts_or_distinctions"]
        != data["modified"]["conflicts_or_distinctions"]
    )
