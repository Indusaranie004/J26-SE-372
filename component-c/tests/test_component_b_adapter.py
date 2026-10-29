"""
Tests for the current Component B -> C PP1
integration contract.

These tests use the exact cluster structure
currently supplied by Component B.

No passage-level retrieval is assumed.
"""

import pytest

from integration.component_b_adapter import (
    component_b_to_reasoning_request,
)


@pytest.fixture
def component_b_payload():

    return {
        "query": (
            "What authorities are relevant "
            "to the legal issue?"
        ),

        "case_facts": [
            (
                "A legal dispute requires "
                "precedent comparison."
            )
        ],

        "reference_date": "2026-10-19",

        "clusters": [
            {
                "seed_id": "case_001",

                "rrf_score": 0.0,

                "cases_cited": [
                    {
                        "target_id": "case_002",
                        "citation_type": "followed",
                        "evidence": "para 12",
                        "scope": "ratio"
                    },
                    {
                        "target_id": "case_003",
                        "citation_type": "distinguished",
                        "evidence": "para 5",
                        "scope": "obiter"
                    },
                    {
                        "target_id": "case_007",
                        "citation_type": "followed",
                        "evidence": "para 8",
                        "scope": "ratio"
                    }
                ],

                "cited_by": [
                    {
                        "target_id": "case_004",
                        "citation_type": "followed",
                        "evidence": "para 3",
                        "scope": None
                    }
                ],

                "legislation": [
                    {
                        "act_id": "leg_001",
                        "name": (
                            "Civil Procedure Code"
                        ),
                        "section": "s.5"
                    }
                ],

                "appeal_chain": [
                    {
                        "related_id": "case_005",
                        "hops": 1
                    },
                    {
                        "related_id": "case_006",
                        "hops": 2
                    }
                ]
            },

            {
                "seed_id": "case_002",

                "rrf_score": 0.0,

                "cases_cited": [
                    {
                        "target_id": "case_007",
                        "citation_type": "followed",
                        "evidence": "para 8",
                        "scope": "ratio"
                    }
                ],

                "cited_by": [],

                "legislation": [
                    {
                        "act_id": "leg_002",
                        "name": (
                            "Evidence Ordinance"
                        ),
                        "section": "s.114"
                    }
                ],

                "appeal_chain": [
                    {
                        "related_id": "case_001",
                        "hops": 1
                    }
                ]
            }
        ]
    }


def test_maps_component_b_clusters(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    assert (
        request.query
        == component_b_payload["query"]
    )

    assert len(request.precedents) == 2

    first = request.precedents[0]

    assert first.case_id == "case_001"

    assert first.relevance_score == 0.0

    # No passage retrieval at PP1.
    assert first.passages == []

    # B has not supplied a validity object.
    assert first.validity is None

    assert (
        first.legislation[0].act_id
        == "leg_001"
    )

    assert (
        first.legislation[0].name
        == "Civil Procedure Code"
    )

    assert (
        first.legislation[0].section
        == "s.5"
    )

    assert (
        first.legislation[0].text
        is None
    )


def test_cases_cited_preserves_outgoing_direction(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    treatment = (
        request
        .precedents[0]
        .judicial_treatments[0]
    )

    assert (
        treatment.source_case_id
        == "case_001"
    )

    assert (
        treatment.target_case_id
        == "case_002"
    )

    assert treatment.status == "followed"

    assert treatment.evidence == "para 12"

    assert treatment.scope == "ratio"

    assert treatment.effective_date is None


def test_cited_by_is_converted_to_incoming_direction(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    incoming = (
        request
        .precedents[0]
        .judicial_treatments[-1]
    )

    assert (
        incoming.source_case_id
        == "case_004"
    )

    assert (
        incoming.target_case_id
        == "case_001"
    )

    assert incoming.status == "followed"

    assert incoming.evidence == "para 3"

    assert incoming.scope is None


def test_sparse_appeal_chain_is_preserved(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    history = (
        request.precedents[0]
        .litigation_history
    )

    assert len(history) == 2

    assert (
        history[0].related_case_id
        == "case_005"
    )

    assert history[0].hops == 1

    assert history[0].court is None

    assert history[0].case_number is None

    assert (
        history[0].source
        == "Component B appeal_chain"
    )


def test_empty_cited_by_is_allowed(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    second = request.precedents[1]

    assert second.case_id == "case_002"

    assert (
        len(second.judicial_treatments)
        == 1
    )


def test_passage_retrieval_is_not_required(
    component_b_payload
):

    request = (
        component_b_to_reasoning_request(
            component_b_payload
        )
    )

    assert all(
        precedent.passages == []
        for precedent in request.precedents
    )


def test_duplicate_seed_ids_are_rejected(
    component_b_payload
):

    component_b_payload[
        "clusters"
    ].append(
        component_b_payload[
            "clusters"
        ][0].copy()
    )

    with pytest.raises(
        ValueError,
        match="duplicate seed_id"
    ):

        component_b_to_reasoning_request(
            component_b_payload
        )