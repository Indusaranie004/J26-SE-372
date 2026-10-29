# Component C — Contextual Reasoning and Legal Draft Generation

## Research Project

**Project:** AI Driven Law Document Analysis System for Sri Lankan Courts  
**Project ID:** J26-SE-372  
**Research Component:** Component C — Contextual Reasoning and Legal Draft Generation  
**Development Stage:** PP1 — Function 1 and Function 2 Implementation

---

## 1. Overview

Component C is responsible for contextual legal reasoning and evidence-grounded legal brief generation using legal precedents and supporting evidence supplied by the upstream research components.

The component acts as the **reasoning and generation stage** of the overall Retrieval-Augmented Generation (RAG) pipeline.

Instead of retrieving legal documents independently, Component C processes supplied legal evidence to produce structured legal analysis and legal research briefs.

### PP1 Implemented Functions

**Function 1 — Cross-Case Contextual & Precedent-Aware Legal Reasoning**

Analyzes multiple legal precedents together, considering:

- Relevant facts and legal questions
- Court hierarchy and judgment chronology
- Judicial-treatment relationships
- Precedent validity information
- Applicable legislation
- Conflicting or distinguishable authorities
- Evidence-supported legal conclusions
- Insufficient or unavailable legal evidence

**Function 2 — Evidence-Grounded Legal Brief Generation**

Transforms legal evidence and contextual reasoning into structured legal research briefs containing:

- Relevant facts and legal issues
- Applicable legislation
- Relevant precedents
- Judicial treatment of precedents
- Legal analysis
- Arguments and counterarguments
- Application of legal principles to facts
- Conclusions and limitations
- Supporting evidence references

Both functions are implemented as research prototypes and exposed through FastAPI endpoints.

**Important:** Current demonstration scenarios use fictional legal cases, facts and legislation. Generated outputs are intended for research and require human legal verification.

---

## 2. Component Responsibilities

The overall research system consists of four interconnected components.

| Component | Responsibility |
|---|---|
| Component A | Legal corpus preparation, knowledge graph construction and legal metadata extraction |
| Component B | Graph-aware legal precedent retrieval and retrieval of relevant legal context |
| Component C | Contextual reasoning, evidence grounding and structured legal brief generation |
| Component D | Intelligent legal issue spotting, argument mapping and citation-strength analysis |

Component C receives retrieved precedent information and processes it into structured legal reasoning and research drafts.

It does not independently perform knowledge graph construction, precedent retrieval or judicial-treatment classification.

### Development Dependencies

During initial PP1 development, controlled fictional legal inputs are used to test Component C independently.

A Component B input adapter has also been implemented to accept the current PP1 retrieval-cluster JSON structure.

However, the existing Component B integration does not yet provide complete judgment passages or statutory text. Missing information is preserved rather than invented, and the resulting analysis is treated as preliminary and metadata-limited.

Full integration with actual upstream legal evidence remains part of future development.

---

## 3. Implemented Architecture

### Function 1 — Contextual Legal Reasoning

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

Function 1 prepares structured legal context, generates cross-case legal reasoning, and validates references to the supplied evidence.

The generated response includes contextual analysis, authority comparisons, a conclusion and relevant limitations.

### Function 2 — Legal Brief Generation

    Original Legal Evidence + Function 1 Reasoning
                          |
                          v
                  BriefGenerationRequest
                          |
                          v
                    Context Builder
                          |
                          v
                  Legal Brief Provider
                          |
                          v
                 Structured LegalBrief
                          |
                          v
                  Grounding Validator
                          |
                          v
                    Evidence Audit
                          |
                          v
                 Legal Research Brief
                          |
                          v
                Markdown / DOCX / PDF

Function 2 reuses the legal evidence and reasoning obtained from Function 1 to generate a structured research brief.

The grounding validator checks references against supplied source identifiers and metadata. The evidence audit provides claim-to-source traceability and identifies selected issues requiring review.

These checks do not independently establish the legal or semantic correctness of generated statements.

---

## 4. Project Structure

### Function 1 — Reasoning

| File | Responsibility |
|---|---|
| `reasoning/input_models.py` | Defines and validates legal reasoning inputs |
| `reasoning/output_models.py` | Defines structured reasoning responses |
| `reasoning/context_builder.py` | Prepares legal evidence for reasoning |
| `reasoning/llm_provider.py` | Defines the replaceable LLM provider interface |
| `reasoning/gemini_provider.py` | Implements Gemini API integration |
| `reasoning/reasoning_service.py` | Coordinates contextual legal reasoning |
| `reasoning/grounding_validator.py` | Validates references against supplied legal evidence |
| `reasoning/result_formatter.py` | Formats structured reasoning into readable output |

### Function 2 — Brief Generation

| File | Responsibility |
|---|---|
| `brief/input_models.py` | Defines legal brief generation inputs |
| `brief/output_models.py` | Defines structured legal brief outputs |
| `brief/context_builder.py` | Prepares evidence and reasoning for drafting |
| `brief/brief_prompt.py` | Defines the legal brief generation prompts |
| `brief/brief_provider.py` | Connects brief generation to Gemini |
| `brief/brief_service.py` | Coordinates legal brief generation |
| `brief/grounding_validator.py` | Checks evidence references in generated briefs |
| `brief/evidence_audit.py` | Produces claim-to-source evidence audits |
| `brief/brief_formatter.py` | Formats generated legal briefs |
| `brief/docx_exporter.py` | Exports legal briefs as Word documents |
| `brief/pdf_exporter.py` | Exports legal briefs as PDF documents |

### API, Integration and Testing

| Directory / File | Responsibility |
|---|---|
| `api/main.py` | Main FastAPI application and reasoning endpoints |
| `api/brief_api.py` | Legal brief generation and export endpoints |
| `api/experiment_demo.py` | Recorded reasoning experiments |
| `api/recorded_demo.py` | Recorded Function 1 demonstrations |
| `api/readable_demo.py` | Human-readable reasoning demonstrations |
| `integration/component_b_models.py` | Component B input schemas |
| `integration/component_b_adapter.py` | Converts Component B clusters into Component C inputs |
| `scripts/` | Experimental and testing utilities |
| `data/demo/` | Recorded fictional demonstration data |
| `docs/` | PP1 documentation and experiment summaries |
| `tests/` | Automated unit and API tests |

---

## 5. Environment Setup

### Prerequisites

- Python 3.13 or a compatible environment
- pip
- Virtual environment
- Gemini API key for live LLM requests
- Visual Studio Code or another Python development environment

### Step 1 — Open the Component Directory

Open PowerShell in the repository and navigate to:

    cd component-c

### Step 2 — Activate the Virtual Environment

If the virtual environment already exists at the repository root:

    ..\.venv\Scripts\Activate.ps1

Alternatively, create a virtual environment inside `component-c`:

    python -m venv .venv

    .\.venv\Scripts\Activate.ps1

### Step 3 — Install Dependencies

    python -m pip install -r requirements.txt

The project uses libraries including:

- FastAPI
- Pydantic
- Google GenAI SDK
- python-dotenv
- pytest
- python-docx
- ReportLab
- pypdf

### Step 4 — Configure Gemini

Create a `.env` file inside the `component-c` directory.

Add:

    GEMINI_API_KEY=your_api_key
    GEMINI_MODEL=your_available_gemini_model_id

Replace the placeholders with your actual credentials and a supported model identifier.

**Do not commit the `.env` file or API credentials to GitHub.**

Live LLM inference requires a configured API key. Recorded demonstrations and offline experiments do not require new Gemini API requests.

---

## 6. Run the Application

Start the FastAPI server from the `component-c` directory:

    python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

Open Swagger UI:

http://127.0.0.1:8000/docs

Health-check endpoint:

http://127.0.0.1:8000/health

### Available API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Verify API availability |
| POST | `/api/reasoning/analyze` | Generate contextual legal reasoning |
| GET | `/api/reasoning/demo/recorded` | Retrieve previously generated reasoning |
| GET | `/api/reasoning/demo/readable` | View recorded reasoning in readable format |
| GET | `/api/reasoning/demo/experiments` | List recorded reasoning experiments |
| GET | `/api/reasoning/demo/experiments/{scenario}` | Retrieve a specific experimental response |
| GET | `/api/reasoning/demo/compare` | Compare recorded reasoning scenarios |
| POST | `/api/brief/generate` | Generate an evidence-grounded legal brief |
| GET | `/api/brief/demo/recorded` | Retrieve a previously generated legal brief |
| GET | `/api/brief/demo/readable` | View a recorded legal brief in Markdown |
| GET | `/api/brief/demo/download/docx` | Download the recorded legal brief as Word |
| GET | `/api/brief/demo/download/pdf` | Download the recorded legal brief as PDF |
| POST | `/api/brief/export/docx` | Export a supplied structured brief as Word |
| POST | `/api/brief/export/pdf` | Export a supplied structured brief as PDF |
| POST | `/api/integration/component-b/reasoning` | Generate reasoning from Component B-style clusters |
| POST | `/api/integration/component-b/brief` | Execute reasoning and brief generation from Component B-style clusters |

POST endpoints that generate new reasoning or briefs require access to the configured LLM provider.

Recorded demonstration endpoints return previously saved outputs and do not perform new LLM inference.

Document export endpoints convert existing structured briefs without calling Gemini.

---

## 7. Function 1 — PP1 Implementation and Experiments

### Implemented Capabilities

Function 1 provides:

1. Structured legal input validation.
2. Cross-case contextual evidence preparation.
3. Precedent-aware and authority-aware reasoning prompts.
4. Court-hierarchy and chronology considerations.
5. Judicial-treatment and validity-context processing.
6. Structured authority comparisons.
7. Evidence-reference grounding validation.
8. FastAPI integration.
9. Recorded experimental demonstrations.

### Controlled Experimental Scenarios

Four fictional scenarios were prepared to evaluate the prototype's behavior under different legal contexts.

| Scenario | Description |
|---|---|
| Scenario 1 — Baseline | Analyzes the original supplied precedent hierarchy and judicial treatment |
| Scenario 2 — Treatment Mutation | Changes judicial treatment and associated validity metadata |
| Scenario 3 — Hierarchy Mutation | Changes fictional court metadata to examine hierarchy-sensitive reasoning |
| Scenario 4 — Insufficient Evidence | Evaluates whether the model recognizes missing evidence for a requested legal remedy |

### Running Experiments

Prepare controlled scenarios:

    python -m scripts.prepare_day2_scenarios

Inspect experiments without making an API call:

    python -m scripts.run_day2_experiments

Inspect a specific scenario:

    python -m scripts.run_day2_experiments --scenario scenario_3_hierarchy_changed

Execute a live Gemini experiment:

    python -m scripts.run_day2_experiments --live --scenario scenario_1_baseline

Live experiments may incur API usage costs.

### Recorded Observations

The four recorded Gemini experiments produced structured legal reasoning responses.

The outputs demonstrated preliminary sensitivity to changes in supplied judicial-treatment information, court metadata and legal evidence availability.

Each recorded experiment populated the four structured authority-comparison fields.

However:

- The treatment experiment changed associated validity metadata as well as treatment.
- The hierarchy experiment used synthetic court metadata.
- Only limited successful responses were evaluated.
- No statistical reliability or general legal-accuracy claims are made.

Recorded experiment results are available in:

`data/demo/live_experiments/`

Detailed documentation:

`data/demo/live_experiments/EXPERIMENT_SUMMARY.md`

---

## 8. Function 2 — PP1 Implementation and Experiments

### Implemented Capabilities

Function 2 provides:

1. Structured legal brief generation.
2. Reuse of Function 1 reasoning and original legal evidence.
3. Claim-level evidence references.
4. Judicial-treatment metadata references.
5. Reference-grounding validation.
6. Claim-to-source evidence auditing.
7. Human-readable Markdown formatting.
8. Word and PDF export.
9. Insufficient-evidence handling.
10. FastAPI endpoints and recorded demonstrations.

### Legal Brief Structure

The generated brief contains:

- Legal issue
- Relevant facts
- Applicable legislation
- Relevant precedents
- Precedent treatment
- Legal analysis
- Arguments
- Counterarguments
- Application to facts
- Conclusion
- Limitations

Each structured legal claim can include evidence references and a support-status classification.

The current reference types include case passages, legislation, original case facts and judicial-treatment metadata.

### Experimental Evaluation

Three recorded experimental outputs were used during Function 2 development.

| Experiment | Claims | Evidence References | Unresolved References | Audit Review Flags |
|---|---:|---:|---:|---:|
| Baseline legal brief | 23 | 39 | 0 | 6 |
| Improved judicial-treatment citation brief | 23 | 39 | 0 | 0 |
| Insufficient-evidence brief | 24 | 35 | 0 | 0 |

The baseline audit identified claims discussing judicial treatment without dedicated treatment references.

The improved implementation introduced a judicial-treatment reference type, improving reference traceability in the recorded scenario.

The insufficient-evidence example generated a qualified conclusion where the supplied authorities did not establish entitlement to financial compensation.

These results are limited to the recorded fictional experiments. The baseline and improved briefs were separate model generations, so the reduction in audit flags does not establish a causal reduction in hallucinations.

### Running Function 2 Experiments

Prepare the baseline brief input without an LLM request:

    python -m scripts.run_brief_experiment

Prepare the insufficient-evidence brief input:

    python -m scripts.run_insufficient_evidence_brief

Generate a baseline evidence-audit report:

    python -m scripts.generate_brief_audit --scenario baseline

Generate an insufficient-evidence audit report:

    python -m scripts.generate_brief_audit --scenario insufficient

Run a new legal brief generation experiment using Gemini:

    python -m scripts.run_brief_experiment --live

The experiment script preserves an existing output file rather than automatically overwriting it.

Recorded legal briefs are stored in:

`data/demo/briefs/`

Generated evidence-audit reports are saved in:

`outputs/brief_audits/`

Detailed experimental documentation:

`docs/FUNCTION_2_PP1_EXPERIMENT_SUMMARY.md`

---

## 9. Testing

Automated tests cover both Function 1 and Function 2.

### Run All Tests

From the `component-c` directory:

    python -m pytest tests/ -q

### Test Coverage Areas

- Input and output model validation
- Context preparation
- LLM provider interfaces
- Reasoning-service behavior
- Judicial-treatment and authority comparisons
- Reference-grounding validation
- Legal brief generation services
- Claim-level evidence reference validation
- Evidence auditing
- Document formatting and export
- API endpoint behavior
- Component B input adaptation and integration paths
- Recorded experimental demonstrations

The Function 2 PP1 experiment documentation recorded **146 passing tests** at that development checkpoint.

Additional test files exist in the current branch. The latest total should be confirmed by running the complete test suite in the configured environment before reporting PP1 results.

Passing automated tests confirms the behavior covered by those tests. It does not independently establish legal correctness or the accuracy of model-generated conclusions.

---

## 10. LLM Integration and Planned Model Comparison

### Current Implementation

The current prototype uses a Gemini-based LLM provider.

The reasoning pipeline includes a replaceable provider interface defined in:

`reasoning/llm_provider.py`

This architecture allows different LLM implementations to be introduced without redesigning the complete contextual reasoning pipeline.

### Planned Comparative Evaluation

According to the research proposal, candidate LLMs for future evaluation include:

- GPT-5
- Gemini 2.5 Flash
- Ministral 3 8B

The intended evaluation will compare models using:

- Citation and grounding accuracy
- Evidence faithfulness
- Unsupported statement rate
- Authority-aware and temporal reasoning correctness
- Legal brief quality
- Response latency
- API usage cost

The final model will be selected based on experimental results rather than assuming that one model performs best.

### Research Baseline Comparison

In addition to comparing LLM providers, the proposed framework will be evaluated against simpler generation approaches:

1. Plain LLM generation without retrieved evidence.
2. Standard RAG generation with retrieved legal evidence.
3. Proposed structured contextual reasoning and evidence-grounded generation framework.

This comparison will evaluate whether the proposed reasoning and grounding mechanisms provide measurable improvements over simpler approaches.

Ablation experiments may also be conducted by removing selected mechanisms, such as judicial-treatment context or claim-level grounding.

**Current PP1 status:** The Gemini implementation and provider abstraction are available. Full multi-model comparison, comprehensive baseline benchmarking and final model selection have not yet been completed.

Optional domain adaptation or fine-tuning experiments are also reserved for later evaluation.

---

## 11. Current Development Status

### Completed for PP1

**Function 1**

- Structured contextual reasoning pipeline
- Gemini provider integration
- Cross-case reasoning and authority comparisons
- Judicial-treatment and chronology-aware context processing
- Evidence-reference grounding validation
- Four recorded experimental scenarios
- FastAPI endpoints
- Automated testing

**Function 2**

- Structured legal research brief generation
- Reuse of Function 1 reasoning outputs
- Claim-level evidence references
- Judicial-treatment reference support
- Grounding validation and evidence auditing
- Recorded legal brief experiments
- Markdown, DOCX and PDF output
- FastAPI endpoints
- Automated testing

**Integration**

- Component B PP1 input models and adapter
- REST endpoints for reasoning over Component B-style clusters
- Combined reasoning and brief-generation API path
- Explicit handling of metadata-only evidence limitations

### Remaining Development and Evaluation

- Full integration with real retrieved legal passages and upstream services
- Evaluation using appropriately sourced real Sri Lankan legal materials
- Broader experimental testing and repeated model runs
- Comparative LLM evaluation and model selection
- Standard RAG and plain LLM baseline comparisons
- More comprehensive claim-to-evidence verification
- Legal domain-expert evaluation
- Performance, reliability and usability evaluation
- Further prompt and grounding refinements

---

## 12. Current Limitations

The PP1 prototype has several important limitations.

1. **Fictional experimental evidence:** Recorded demonstrations currently use fictional cases, legislation and legal scenarios.

2. **Incomplete upstream integration:** The current Component B PP1 adapter supports structured cluster metadata, but the upstream data does not yet include complete judgment passages.

3. **Structural grounding validation:** Current validators check identifiers, reference ownership and selected metadata relationships. They do not provide complete semantic verification that a source legally supports every generated claim.

4. **Model reliability:** Gemini responses may vary between executions, and live inference depends on provider availability and API configuration.

5. **Limited experimental scale:** Current recorded experiments are preliminary and do not establish statistically reliable model performance.

6. **Pending model comparison:** The proposed multi-LLM and baseline evaluations remain future research activities.

7. **Human verification requirement:** Court hierarchy, judicial treatment, statutory interpretation and final legal conclusions require review against authoritative legal sources.

These limitations will be addressed through subsequent development, integration and controlled research evaluation.

---

## 13. PP1 Demonstration Guide

### Function 1

1. Start the FastAPI application.
2. Open Swagger UI.
3. Execute the health-check endpoint.
4. List the four recorded reasoning experiments.
5. Demonstrate the baseline reasoning response.
6. Compare baseline and treatment-modified responses.
7. Demonstrate the hierarchy-modified scenario.
8. Demonstrate how insufficient evidence is handled.
9. Explain the grounding validator and structured reasoning output.

### Function 2

1. Retrieve the recorded legal brief.
2. Display the human-readable Markdown version.
3. Explain the brief structure and evidence references.
4. Demonstrate judicial-treatment citations.
5. Present the evidence-audit results.
6. Download the recorded legal brief as DOCX.
7. Download the recorded legal brief as PDF.
8. Explain the current limitations of citation validation.

### Supporting Evidence

PP1 supporting materials include:

- Automated test results
- Recorded reasoning experiment outputs
- Function 2 experiment summary
- Source and grounding validation code
- Component architecture
- GitHub development history
- Research diary and implementation notes

---

## 14. Future Development

The next stages will focus on:

- Integrating actual outputs from Components A and B
- Improving cross-case reasoning using real legal evidence
- Refining judicial-treatment and temporal reasoning
- Expanding claim-level grounding and verification
- Evaluating alternative LLMs
- Comparing the proposed framework against simpler generation baselines
- Performing legal-expert validation
- Improving reliability, performance and document quality

The final goal is to develop and evaluate an explainable, evidence-grounded legal reasoning framework that assists Sri Lankan legal practitioners in reviewing precedents and preparing structured legal research briefs.

---

## Research Disclaimer

This component is developed for academic research and prototype evaluation.

AI-generated analyses and legal briefs are **research-support outputs**, not authoritative legal advice or court-ready legal submissions.

All generated conclusions and supporting citations must be reviewed by a qualified human against the relevant legal sources before professional use.
