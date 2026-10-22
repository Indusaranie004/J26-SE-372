import pytest
from pydantic import ValidationError

from reasoning.output_models import ReasoningResponse

def sample_reasoning_output():
    return{
        "legal_issue": "Whether prior notice is required before permit revocation",

        "relevant_facts": [
            "The business received no prior notice.",
            "No emergency was identified."
        ],

        "authorities": [
            {
                "case_id": "MOCK_SC_001",
                "case_name": "Mock Business Association v. Public Authority",
                "court": "Supreme Court",
                "relevance_to_issue": "Addresses prior notice requirements.",
                "validity_status": "good_law",
                "judicial_treatment_summary": "Followed by a later mock decision.",
                "authority_assessment": "Relevant to ordinary permit revocations.",
                "supporting_evidence": [
                    {
                        "case_id": "MOCK_SC_001",
                        "passage_id": "P1"
                    }
                ]
            }
        ],

        "cross_case_analysis": "The supplied authority supports prior notice.",

        "legislation_considered": [
            "Mock Fair Administrative Procedure Act, Section 10"
        ],

        "application": "The current facts involve no identified emergency.",

        "conclusion": "The supplied evidence supports a prior notice requirement.",

       "limitations_or_insufficient_evidence": [
            "This analysis uses fictional development data."
        ] 
    }

def test_valid_reasoning_output():
    data = sample_reasoning_output()

    result = ReasoningResponse.model_validate(data)

    assert result.authorities[0].case_id == "MOCK_SC_001"
    assert result.authorities[0].validity_status == "good_law"
    assert result.authorities[0].supporting_evidence[0].passage_id == "P1"

def test_invalid_validity_status():
    data = sample_reasoning_output()

    data["authorities"][0]["validity_status"] = "always_binding"

    with pytest.raises(ValidationError):
        ReasoningResponse.model_validate(data)