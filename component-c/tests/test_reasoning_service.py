
"""
Tests for the complete reasoning service.

Uses a fake LLM provider to avoid API costs.
"""

import json
from pathlib import Path

import pytest

from reasoning.input_models import ReasoningRequest
from reasoning.llm_provider import LLMProvider
from reasoning.reasoning_service import run_cross_case_reasoning


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "reasoning"
    / "data"
    / "mock_case_data.json"
)


class FakeLLMProvider(LLMProvider):
    """A controlled LLM provider for automated tests."""

    def __init__(self, response_data):
        self.response_data = response_data
        self.last_user_prompt = None

    def generate(self, system_prompt, user_prompt):
        self.last_user_prompt = user_prompt

        return json.dumps(self.response_data)


@pytest.fixture
def reasoning_request():
    return ReasoningRequest.model_validate_json(
        DATA_FILE.read_text(encoding="utf-8")
    )


@pytest.fixture
def valid_response_data(reasoning_request):

    authorities = []

    for precedent in reasoning_request.precedents:

        authorities.append({
            "case_id": precedent.case_id,
            "relevance_to_issue": "Relevant to the issue.",
            "validity_status": precedent.validity.status,
            "judicial_treatment_summary": "Treatment considered.",
            "authority_assessment": "Based on supplied evidence.",
            "supporting_evidence": [
                {
                    "case_id": precedent.case_id,
                    "passage_id": passage.passage_id
                }
                for passage in precedent.passages
            ]
        })

    return {
        "legal_issue": reasoning_request.query,
        "authorities": authorities,
        "cross_case_analysis": "Cross-case analysis.",
        "application": "Application to the facts.",
        "conclusion": "Test conclusion."
    }


def test_pipeline_accepts_grounded_response(
    reasoning_request,
    valid_response_data
):
    provider = FakeLLMProvider(valid_response_data)

    result = run_cross_case_reasoning(
        reasoning_request,
        provider
    )

    assert len(result.authorities) == 3
    assert result.authorities[0].case_id == "MOCK_SC_001"

    # verify the actual evidence context reached the provider
    assert "MOCK_SC_001" in provider.last_user_prompt
    assert "MOCK_CA_002" in provider.last_user_prompt


def test_pipeline_rejects_invented_passage(
    reasoning_request,
    valid_response_data
):
    valid_response_data["authorities"][0]["supporting_evidence"][0][
        "passage_id"
    ] = "FAKE_P999"

    provider = FakeLLMProvider(valid_response_data)

    with pytest.raises(ValueError, match="Unknown passage"):
        run_cross_case_reasoning(
            reasoning_request,
            provider
        )


def test_pipeline_rejects_wrong_validity(
    reasoning_request,
    valid_response_data
):
    valid_response_data["authorities"][2][
        "validity_status"
    ] = "good_law"

    provider = FakeLLMProvider(valid_response_data)

    with pytest.raises(ValueError, match="Validity mismatch"):
        run_cross_case_reasoning(
            reasoning_request,
            provider
        )
