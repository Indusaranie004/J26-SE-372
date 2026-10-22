
"""
Tests for the version-controlled demonstration fixture.

Ensures a fresh project checkout contains a valid
recorded response that FastAPI can load.

No Gemini API calls are made.
"""

from fastapi.testclient import TestClient

from api.main import app
from api.recorded_demo import RECORDED_RESULT_FILE

from reasoning.output_models import ReasoningResponse


def test_recorded_fixture_exists_and_is_valid():
    """
    The recorded demonstration must be available
    independently of the ignored outputs folder.
    """

    assert RECORDED_RESULT_FILE.is_file()

    saved_json = RECORDED_RESULT_FILE.read_text(
        encoding="utf-8"
    )

    result = ReasoningResponse.model_validate_json(
        saved_json
    )

    assert len(result.authorities) == 3

    assert result.legal_issue

    assert result.conclusion


def test_recorded_endpoint_loads_fixture():
    """
    Verify that the actual configured fixture
    is returned through FastAPI.
    """

    with TestClient(app) as client:
        response = client.get(
            "/api/reasoning/demo/recorded"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "recorded"

    assert data["comparison_available"] is False

    assert len(data["result"]["authorities"]) == 3

    assert "not a live Gemini result" in data["note"]
