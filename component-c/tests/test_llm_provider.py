
import json

import pytest
from pydantic import ValidationError

from reasoning.llm_provider import (
    LLMProvider,
    parse_reasoning_output
)


def test_abstract_provider_cannot_be_instantiated():

    with pytest.raises(TypeError):
        LLMProvider()


def test_valid_llm_json_response():

    mock_response = {
        "legal_issue": "Whether prior notice is required",
        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "relevance_to_issue": "Addresses prior notice.",
                "judicial_treatment_summary": "Followed.",
                "authority_assessment": "Relevant authority."
            }
        ],
        "cross_case_analysis": "The authority supports notice.",
        "application": "No emergency was identified.",
        "conclusion": "Prior notice appears required."
    }

    raw_json = json.dumps(mock_response)

    result = parse_reasoning_output(raw_json)

    assert result.legal_issue == mock_response["legal_issue"]
    assert result.authorities[0].case_id == "MOCK_SC_001"


def test_invalid_llm_json_response():

    invalid_json = '{"legal_issue": "Test"}'

    with pytest.raises(ValidationError):
        parse_reasoning_output(invalid_json)
