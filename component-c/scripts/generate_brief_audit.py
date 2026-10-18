
"""
Component C - Function 2
Recorded Legal Brief Evidence Audit

Generates JSON and Markdown evidence audits
from existing fictional development experiments.

No Gemini API calls are made.

Usage:

python -m scripts.generate_brief_audit --scenario baseline

python -m scripts.generate_brief_audit --scenario insufficient
"""

import argparse
from pathlib import Path

from brief.output_models import LegalBrief

from brief.evidence_audit import (
    create_evidence_audit,
    format_evidence_audit,
)

from scripts.run_brief_experiment import (
    prepare_brief_request,
)

from scripts.run_insufficient_evidence_brief import (
    prepare_request as prepare_insufficient_request,
)


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = BASE_DIR / "data" / "demo" / "briefs"

OUTPUT_DIR = BASE_DIR / "outputs" / "brief_audits"


SCENARIOS = {
    "baseline": {
        "filename": "baseline_legal_brief.json",
        "prepare": prepare_brief_request,
    },
    "insufficient": {
        "filename": "insufficient_evidence_legal_brief.json",
        "prepare": prepare_insufficient_request,
    },
}


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate a claim-to-evidence audit "
            "for a recorded legal brief."
        )
    )

    parser.add_argument(
        "--scenario",
        choices=SCENARIOS.keys(),
        required=True,
    )

    args = parser.parse_args()

    configuration = SCENARIOS[args.scenario]

    request = configuration["prepare"]()

    input_path = (
        INPUT_DIR / configuration["filename"]
    )

    brief = LegalBrief.model_validate_json(
        input_path.read_text(encoding="utf-8")
    )

    audit = create_evidence_audit(
        request,
        brief,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        OUTPUT_DIR / f"{args.scenario}_audit.json"
    )

    markdown_path = (
        OUTPUT_DIR / f"{args.scenario}_audit.md"
    )

    json_path.write_text(
        audit.model_dump_json(indent=2),
        encoding="utf-8",
    )

    markdown_path.write_text(
        format_evidence_audit(audit),
        encoding="utf-8",
    )

    print("=" * 55)
    print("FUNCTION 2 - EVIDENCE AUDIT")
    print("=" * 55)

    print("Scenario:", args.scenario)
    print("Claims:", audit.total_claims)
    print("References:", audit.total_references)
    print(
        "Unresolved references:",
        audit.unresolved_references,
    )
    print(
        "Claims with review flags:",
        audit.flagged_claims,
    )

    print("\nJSON report:", json_path.resolve())
    print("Markdown report:", markdown_path.resolve())

    print("\nAudit generation completed.")
    print(
        "Citation existence does not establish "
        "semantic or legal correctness."
    )


if __name__ == "__main__":
    main()
