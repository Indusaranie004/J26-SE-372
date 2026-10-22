# Function 1 — PP1 Prototype Demonstration Checklist

**Research Project:** AI Driven Law Document Analysis System for Sri Lankan Courts  
**Component:** Contextual Reasoning and Legal Draft Generation  
**Function 1:** Cross-Case Contextual & Precedent-Aware Legal Reasoning

## 1. Demonstration Objective

Demonstrate that Component C can analyze supplied legal precedents using judicial-treatment metadata, court hierarchy, chronological information, case facts and available legal evidence.

The demonstration uses fictional legal cases and previously recorded Gemini responses.

It does not require live access to Gemini.

## 2. Start the Application

Open a terminal inside the `component-c` directory.

Activate the project's virtual environment if necessary.

Start the API:

`python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000`

Open Swagger:

`http://127.0.0.1:8000/docs`

## 3. Demonstration Checklist

- [ ] **Health check:** Execute `GET /health` and confirm HTTP 200.
- [ ] **Experiment listing:** Execute `GET /api/reasoning/demo/experiments` and confirm that all four experiments are available.
- [ ] **Baseline reasoning:** Execute `GET /api/reasoning/demo/experiments/scenario_1_baseline` and explain the three fictional precedents.
- [ ] **Treatment mutation:** Execute `GET /api/reasoning/demo/experiments/scenario_2_treatment_changed` and show how `MOCK_SC_003` is now treated as good law.
- [ ] **Recorded comparison:** Execute `GET /api/reasoning/demo/compare` and demonstrate the difference between the two saved outputs.
- [ ] **Hierarchy mutation:** Execute `GET /api/reasoning/demo/experiments/scenario_3_hierarchy_changed` and explain why the hierarchy discussion changes.
- [ ] **Insufficient evidence:** Execute `GET /api/reasoning/demo/experiments/scenario_4_insufficient_evidence` and show the model's acknowledgement that compensation entitlement cannot be established.
- [ ] **Readable report:** Execute `GET /api/reasoning/demo/readable`. This endpoint displays the older Day 1 recorded response, not the four newer experimental outputs.
- [ ] **Automated tests:** Run `python -m pytest tests/ -q`.

## 4. Key Research Findings

| Scenario | Experimental modification | Observed result |
|---|---|---|
| Baseline | Original supplied precedents | Generated cross-case analysis with hierarchy, chronology and judicial treatment |
| Treatment mutation | Changed overruling and validity metadata | Identified an unresolved conflict between active Supreme Court authorities |
| Hierarchy mutation | Changed court metadata for one precedent | Updated hierarchy discussion while preserving the relevant factual distinction |
| Insufficient evidence | Changed the legal question to compensation | Reported insufficient evidence rather than inventing a compensation entitlement |

All four recorded responses populated the four structured authority-comparison fields.

These are preliminary observations from fictional scenarios, not statistical measurements of legal accuracy.

## 5. Main Architecture

The reasoning workflow is:

**Validated Request → Context Builder → Gemini Provider → Structured Response Parser → Grounding Validator → Reasoning Response**

The API exposes the existing reasoning service rather than duplicating the reasoning logic.

The recorded demonstration endpoints read previously saved results without generating new responses.

## 6. Verification and Validation

Current automated test suite: **68 passing tests**.

Implemented checks include structured-output validation, expected case identifiers, referenced passage identifiers and consistency with supplied validity metadata.

These checks do not guarantee that every generated legal statement is semantically correct.

## 7. Known Limitations

- All demonstration cases and legislation are fictional.
- The four original successful experiments involved one recorded model response per scenario.
- Judicial-treatment mutation also changed associated validity metadata.
- The hierarchy mutation used synthetic court metadata.
- Some original outputs contained broad statements about overruling or missing statutory information.
- The system prompt has been refined to address these weaknesses, but a new successful live evaluation is still pending.
- The latest refined-prompt experiment encountered Gemini HTTP 503.
- The system has not yet completed integration with Components A and B.
- This prototype is not suitable for real legal advice or unsupervised legal decisions.

## 8. Evidence to Capture for PP1

- Swagger API overview
- Successful `GET /health` response
- List of four recorded experiments
- Baseline and modified judicial-treatment comparison
- Insufficient-evidence conclusion
- Terminal screenshot showing passing automated tests
- GitHub branch and commit history
- Experimental results documentation

Avoid including API keys, `.env` contents or other credentials in screenshots.

## 9. Function 1 Completion Status

**Completed:** Reasoning pipeline, Gemini integration, structured response generation, court hierarchy and temporal context handling, grounding checks, controlled experiments, FastAPI endpoints, recorded demonstration and automated tests.

**Pending:** Repeatable live evaluation of the refined prompt, broader research-quality assessment and integration with other components.

The initial Function 1 PP1 prototype is substantially implemented and can be demonstrated using recorded fictional experiments.

## 10. Next Development Stage

Proceed to **Function 2 — Evidence-Grounded Legal Brief Generation**.

Function 2 will reuse Function 1's validated reasoning response and supporting evidence references to generate a structured legal brief with traceable claims and additional evidence-validation checks.