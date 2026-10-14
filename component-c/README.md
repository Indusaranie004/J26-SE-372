
# Component C — Contextual Reasoning and Legal Draft Generation

## Research Project

AI Driven Law Document Analysis System for Sri Lankan Courts

**Research Component:** Component C  
**Current Development:** PP1 — Function 1  
**Branch:** feature/C-1-reasoning

## 1. Overview

Component C is responsible for reasoning over legal evidence
supplied by the upstream research components.

The current prototype implements:

**Cross-Case Contextual & Precedent-Aware Legal Reasoning**

It analyzes multiple supplied precedents together, considering:

- Relevant facts and legal questions
- Judgment passages
- Court hierarchy
- Judgment chronology
- Judicial-treatment relationships
- Precedent validity metadata
- Supplied legislation
- Conflicting or distinguishable authorities
- Application of legal principles to supplied facts

The output is a structured legal analysis.

All current demonstration cases are fictional.

## 2. Component Responsibilities

Component A will eventually supply extracted legal metadata,
including court information, judgment dates, legislation,
litigation history and judicial-treatment relationships.

Component B will eventually supply retrieved precedents,
relevant passages and relevance information.

Component C consumes these inputs and produces structured
cross-case reasoning.

The current prototype uses controlled mock inputs because
the upstream integrations are not yet complete.

Component C does not perform precedent retrieval,
knowledge-graph construction or judicial-treatment classification.

## 3. Implemented Architecture

Legal Question + Case Facts + Supplied Precedents
                     |
                     v
              ReasoningRequest
                     |
                     v
              Context Builder
                     |
                     v
              Reasoning Service
                     |
                     v
              Gemini LLM Provider
                     |
                     v
           Structured Output Parser
                     |
                     v
             Grounding Validator
                     |
                     v
              ReasoningResponse

FastAPI exposes the existing reasoning service through a REST API.

## 4. Main Project Files

| File | Responsibility |
|------|----------------|
| reasoning/input_models.py | Validates legal input data |
| reasoning/output_models.py | Defines structured reasoning output |
| reasoning/context_builder.py | Prepares supplied legal context |
| reasoning/llm_provider.py | Defines the replaceable LLM interface |
| reasoning/gemini_provider.py | Connects the pipeline to Gemini |
| reasoning/reasoning_service.py | Coordinates contextual reasoning |
| reasoning/grounding_validator.py | Checks case IDs, passage IDs and validity metadata |
| reasoning/result_formatter.py | Converts structured results into readable text |
| api/main.py | FastAPI application and live reasoning endpoint |
| api/recorded_demo.py | Returns previously generated reasoning |
| api/readable_demo.py | Displays recorded reasoning in readable format |
| scripts/prepare_day2_scenarios.py | Generates controlled experimental scenarios |
| scripts/run_day2_experiments.py | Runs experiments in offline or live mode |

## 5. Environment Setup

Use Python 3.13 or a compatible environment.

Open PowerShell in the component-c directory.

Activate the existing project virtual environment:

    ..\.venv\Scripts\Activate.ps1

Install the required dependencies:

    python -m pip install -r requirements.txt

For live Gemini execution, configure a local .env file
inside component-c containing:

    GEMINI_API_KEY=your_api_key
    GEMINI_MODEL=your_configured_model

Do not commit the .env file or any API credentials.

Recorded demonstration endpoints do not require a Gemini API key.

## 6. Run the API

Start the FastAPI server:

    python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

Open Swagger:

    http://127.0.0.1:8000/docs

Available endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /health | Check API availability |
| POST | /api/reasoning/analyze | Generate a new legal analysis |
| GET | /api/reasoning/demo/recorded | Retrieve a saved analysis |
| GET | /api/reasoning/demo/readable | View saved analysis as readable text |

The live reasoning endpoint requires Gemini availability.

The recorded endpoints are offline demonstrations and
do not perform new LLM inference.

## 7. Controlled Experimental Scenarios

Four fictional scenarios are available:

1. Baseline — original judicial-treatment metadata
2. Treatment mutation — changed treatment and related validity metadata
3. Hierarchy mutation — changed fictional court metadata
4. Insufficient evidence — question not resolved by supplied evidence

Generate the scenario inputs:

    python -m scripts.prepare_day2_scenarios

Inspect the scenarios without calling Gemini:

    python -m scripts.run_day2_experiments

Inspect one scenario:

    python -m scripts.run_day2_experiments --scenario scenario_3_hierarchy_changed

To execute the baseline through Gemini:

    python -m scripts.run_day2_experiments --live --scenario scenario_1_baseline

Live execution makes external API requests and may incur usage costs.

The treatment experiment changes both treatment and associated
validity metadata, so its results cannot isolate the influence
of the treatment label alone.

## 8. Testing

Run all automated tests:

    python -m pytest tests/ -q

Latest verified test result:

    61 passed

Tests cover input/output validation, context preparation,
reasoning service behavior, grounding checks, experimental
scenarios, FastAPI endpoints and recorded demonstrations.

Passing tests demonstrate implemented software behavior.
They do not establish the legal correctness of model-generated
conclusions.

## 9. Recorded Demonstration

A previously generated fictional Day 1 response is stored in:

    data/demo/day1_baseline_response.json

It can be viewed through:

    GET /api/reasoning/demo/recorded

Or as readable text:

    GET /api/reasoning/demo/readable

This output is explicitly identified as recorded and is not
presented as a newly generated Gemini response.

The Day 1 result predates the four structured authority
comparison fields introduced on Day 2.

## 10. Current Limitations

- Gemini has repeatedly returned HTTP 503 during recent live tests.
- The Day 2 structured comparison has not yet been verified
  through a successful live model response.
- Recorded Day 1 output remains available for offline demonstration.
- Current grounding validation checks structural references and
  metadata consistency, not complete legal correctness.
- Controlled scenarios use fictional cases and legislation.
- Component A and B live integrations are pending.
- Legal brief generation (Function 2) is not implemented.
- Multi-LLM comparison and fine-tuning are deferred.

## 11. Research Development Status

Day 1:
Implemented the foundational reasoning pipeline, Gemini provider,
structured responses and basic grounding validation.

Day 2:
Improved contextual reasoning, temporal treatment handling,
authority-aware prompting, structured authority comparison,
controlled scenarios and experiment execution.

Day 3:
Implemented FastAPI, Swagger documentation, API error handling,
a portable recorded demonstration and human-readable report formatting.

The current PP1 prototype demonstrates the architecture and
validated software pipeline for Function 1.

Further live experiments and evaluation are required to
demonstrate how changes in judicial-treatment metadata
influence generated reasoning.
