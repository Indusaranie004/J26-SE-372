
"""
Tests for the authority-aware legal reasoning prompt.

Checks prompt requirements and verifies that the
reasoning service forwards the correct instructions
to the LLM provider.

No actual Gemini API requests are made.
"""

import json

from reasoning.input_models import ReasoningRequest
from reasoning.llm_provider import LLMProvider
from reasoning.reasoning_service import (
    LEGAL_REASONING_SYSTEM_PROMPT,
    run_cross_case_reasoning,
)


def test_prompt_requires_cross_case_synthesis():
    """The prompt must require analysis across authorities."""

    prompt = LEGAL_REASONING_SYSTEM_PROMPT.lower()

    assert "cross-case" in prompt
    assert "not merely summarize" in prompt
    assert "compare the authorities" in prompt
    assert "conflict" in prompt


def test_prompt_includes_authority_rules():
    """The prompt must address legal-context metadata."""

    prompt = LEGAL_REASONING_SYSTEM_PROMPT

    assert "COURT HIERARCHY" in prompt
    assert "CHRONOLOGY AND REFERENCE DATE" in prompt

    assert "FOLLOWED:" in prompt
    assert "DISTINGUISHED:" in prompt
    assert "OVERRULED:" in prompt
    assert "CRITICIZED OR DOUBTED:" in prompt

    assert "source_case_id --status--> target_case_id" in prompt

    assert "AFTER the reference date" in prompt
    assert "scope of the overruling" in prompt


def test_prompt_includes_evidence_safeguards():
    """The prompt must discourage unsupported conclusions."""

    prompt = LEGAL_REASONING_SYSTEM_PROMPT.lower()

    assert "never invent" in prompt

    assert "only supplied case ids and passage ids" in prompt

    assert "do not force a yes/no conclusion" in prompt

    assert "insufficient evidence" in prompt

    assert "fictional development" in prompt


class RecordingProvider(LLMProvider):
    """Fake provider that records instructions sent to it."""

    def __init__(self):
        self.received_system_prompt = None
        self.received_user_prompt = None

    def generate(self, system_prompt, user_prompt):

        self.received_system_prompt = system_prompt
        self.received_user_prompt = user_prompt

        mock_response = {
            "legal_issue": "Test legal question",
            "relevant_facts": [],
            "authorities": [
                {
                    "case_id": "MOCK_SC_001",
                    "relevance_to_issue": "Test relevance.",
                    "validity_status": "unknown",
                    "judicial_treatment_summary": (
                        "No treatment supplied."
                    ),
                    "authority_assessment": (
                        "Insufficient evidence."
                    ),
                    "supporting_evidence": []
                }
            ],
            "cross_case_analysis": (
                "Only one authority was supplied."
            ),
            "legislation_considered": [],
            "application": "Insufficient evidence.",
            "conclusion": (
                "The supplied evidence is insufficient."
            ),
            "limitations_or_insufficient_evidence": [
                "No judgment passages were supplied."
            ]
        }

        return json.dumps(mock_response)


def test_service_sends_correct_prompt_to_provider():
    """The service must forward the correct prompt."""

    reasoning_request = ReasoningRequest.model_validate({
        "query": "Is prior notice required?",
        "case_facts": [],
        "precedents": [
            {
                "case_id": "MOCK_SC_001"
            }
        ]
    })

    provider = RecordingProvider()

    result = run_cross_case_reasoning(
        reasoning_request,
        provider
    )

    assert (
        provider.received_system_prompt
        == LEGAL_REASONING_SYSTEM_PROMPT
    )

    assert (
        "Is prior notice required?"
        in provider.received_user_prompt
    )

    assert "MOCK_SC_001" in provider.received_user_prompt

    assert result.authorities[0].case_id == "MOCK_SC_001"
