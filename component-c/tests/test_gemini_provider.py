
"""
Tests for the Gemini LLM provider.

Uses a mocked API client to avoid real API requests.
"""

import json
from unittest.mock import patch

import pytest

from reasoning.gemini_provider import GeminiProvider
from reasoning.llm_provider import (
    LLMProvider,
    parse_reasoning_output
)


def mock_reasoning_response():
    return {
        "legal_issue": "Whether prior notice is required",

        "relevant_facts": [
            "No prior notice was given."
        ],

        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "relevance_to_issue": "Addresses prior notice.",
                "validity_status": "good_law",
                "judicial_treatment_summary": "Followed.",
                "authority_assessment": "Relevant authority.",
                "supporting_evidence": [
                    {
                        "case_id": "MOCK_SC_001",
                        "passage_id": "P1"
                    }
                ]
            }
        ],

        "cross_case_analysis": "The authority supports notice.",

        "legislation_considered": [],

        "application": "No emergency was identified.",

        "conclusion": "Notice appears to be required.",

        "limitations_or_insufficient_evidence": []
    }


@patch("reasoning.gemini_provider.genai.Client")
def test_gemini_provider_generates_structured_response(mock_client_class):

    # configure the fake Gemini API client
    mock_client = mock_client_class.return_value

    mock_client.models.generate_content.return_value.text = (
        json.dumps(mock_reasoning_response())
    )

    provider = GeminiProvider(
        api_key="fake-test-key",
        model="gemini-3.8-flash"
    )

    assert isinstance(provider, LLMProvider)

    # generate a response using the mocked client
    raw_output = provider.generate(
        system_prompt="Analyze legal evidence.",
        user_prompt="Analyze MOCK_SC_001."
    )

    # validate the returned JSON
    result = parse_reasoning_output(raw_output)

    assert result.authorities[0].case_id == "MOCK_SC_001"
    assert result.authorities[0].validity_status == "good_law"

    # confirm the correct prompts were sent
    call_args = mock_client.models.generate_content.call_args

    assert call_args.kwargs["contents"] == "Analyze MOCK_SC_001."

    config = call_args.kwargs["config"]

    assert config.system_instruction == "Analyze legal evidence."
    assert config.response_mime_type == "application/json"


@patch("reasoning.gemini_provider.genai.Client")
def test_gemini_provider_handles_empty_response(mock_client_class):

    mock_client = mock_client_class.return_value

    mock_client.models.generate_content.return_value.text = None

    provider = GeminiProvider(api_key="fake-test-key")

    with pytest.raises(RuntimeError):
        provider.generate(
            system_prompt="Test",
            user_prompt="Test"
        )
