
# Component C — Function 1 Experimental Results

## 1. Research Component

Project: AI Driven Law Document Analysis System
for Sri Lankan Courts

Component: Contextual Reasoning and Legal Draft Generation

Function 1:
Cross-Case Contextual & Precedent-Aware Legal Reasoning

## 2. Experimental Objective

The purpose of these experiments is to investigate
whether the reasoning component responds appropriately
to changes in supplied legal context.

The evaluation focuses on:

- Judicial-treatment awareness
- Court hierarchy awareness
- Chronological reasoning
- Cross-case conflict identification
- Recognition of insufficient legal evidence

All experiments use fictional legal precedents.
The results do not represent real Sri Lankan law.

## 3. Experimental Configuration

LLM: Gemini
Configured model: gemini-3.8-flash

Input format: ReasoningRequest (Pydantic)

Output format: ReasoningResponse (Pydantic)

Reference date: 2026-10-12

Precedents per scenario: 3

Execution:
python -m scripts.run_day2_experiments --live

Validation:
- Pydantic structured-output validation
- Authority ID validation
- Passage ID validation
- Supplied validity-status consistency checks

The four recorded responses passed the implemented
software validation pipeline.

These checks do not independently verify the
legal correctness of generated explanations.

## 4. Scenario 1 — Baseline

Input:

MOCK_SC_001:
- Supreme Court
- Good law
- Followed by MOCK_SC_004

MOCK_CA_002:
- Court of Appeal
- Partially invalidated
- Distinguished by MOCK_SC_005

MOCK_SC_003:
- Supreme Court
- No longer good law
- Overruled by MOCK_SC_006

Observed result:

The model recognized the supplied judicial-treatment
relationships and the emergency distinction.

It treated the overruled proposition in MOCK_SC_003
as unavailable as current authority for the
relevant procedural issue.

The conclusion supported prior notice and an
opportunity to respond in the non-emergency scenario.

Structured comparison fields: 4/4 populated.

## 5. Scenario 2 — Treatment Mutation

Modification:

The supplied treatment of MOCK_SC_003 changed from
OVERRULED to FOLLOWED.

Associated validity and treatment-description metadata
were also changed to maintain a coherent fictional
test scenario.

Observed result:

The model recognized MOCK_SC_003 as an active,
conflicting Supreme Court authority.

Unlike the baseline, it identified an unresolved
conflict between MOCK_SC_001 and MOCK_SC_003.

The final analysis acknowledged uncertainty while
noting that MOCK_SC_001 aligned with the supplied
statutory provision.

Structured comparison fields: 4/4 populated.

Interpretation:

The observed response changed appropriately when
the treatment and associated validity metadata
were modified.

Limitation:

This experiment does not isolate the effect of the
judicial-treatment label alone because multiple
related metadata fields changed together.

## 6. Scenario 3 — Hierarchy Mutation

Modification:

The supplied court of MOCK_CA_002 changed from
Court of Appeal to Supreme Court.

The fictional case number was also changed.

The underlying precedent passages, validity and
judicial-treatment data remained unchanged.

Observed result:

The model recognized all three supplied precedents
as Supreme Court decisions.

It updated the hierarchy comparison accordingly.

It continued to distinguish the emergency exception
from ordinary non-emergency revocations.

The final conclusion remained consistent with
the baseline scenario.

Structured comparison fields: 4/4 populated.

Interpretation:

The model demonstrated sensitivity to the changed
court metadata without automatically changing
the conclusion.

Limitation:

The court reassignment was entirely synthetic.
The internal case ID remained stable to support
before-and-after comparison.

## 7. Scenario 4 — Insufficient Evidence

Modification:

The legal question changed to whether the business
was entitled to financial compensation for lost
income following the permit revocation.

The supplied precedents remained unchanged.

Observed result:

The model distinguished procedural unfairness from
an entitlement to monetary compensation.

It identified the absence of legal authorities
establishing financial remedies.

The conclusion stated that the supplied evidence
was insufficient to determine compensation entitlement.

Structured comparison fields: 4/4 populated.

Interpretation:

The model demonstrated appropriate uncertainty
for this fictional test question.

## 8. Overall Observations

All four recorded experiments:

- Produced structured reasoning responses.
- Included analyses of all three supplied precedents.
- Populated the four authority-comparison fields.
- Passed the implemented structural grounding checks.

The experiments provided preliminary evidence of
context-sensitive behavior.

In particular:

1. Changes to treatment and validity metadata
   influenced the authority assessment and
   conflict analysis.

2. A change to court metadata influenced hierarchy
   discussion without necessarily changing the
   final legal conclusion.

3. The model recognized insufficient evidence
   for a financial-compensation question.

## 9. Identified Weaknesses

### Judicial-treatment scope

Some generated statements used broad wording such as
a precedent being completely overruled.

The supplied metadata identified a specific scope.

Future improvements should encourage conclusions
that preserve the scope of judicial treatment.

### Statutory evidence interpretation

Some responses described statutory text as incomplete
because it was not repeated under every precedent.

The context builder already provides shared statutory
evidence where available.

Future improvements should distinguish missing
statutory text from text that is simply not repeated
in every precedent record.

### Legal authority characterization

Some responses used strong descriptions such as
governing or prevailing precedent.

Such statements require caution when detailed
jurisdiction-specific priority rules have not been
supplied.

## 10. Evaluation Limitations

- Only one recorded successful response per scenario
  has been evaluated here.
- Responses may vary between repeated model runs.
- No controlled random seed or decoding configuration
  was recorded for these runs.
- The treatment mutation changed several related
  metadata fields.
- The hierarchy mutation used synthetic court metadata.
- All legal evidence is fictional.
- Current grounding checks verify structural consistency,
  not complete semantic or legal correctness.
- No comparison with alternative LLMs was performed.
- No statistical reliability metrics were calculated.
- Actual Component A and Component B integrations
  remain pending.

## 11. Conclusion

These preliminary experiments indicate that the
Component C Function 1 prototype can generate
structured cross-case analyses that respond to
changes in supplied legal metadata.

The results support further investigation of
contextual reasoning, judicial-treatment awareness,
and evidence insufficiency detection.

They do not establish general legal accuracy,
reliability or real-world suitability.

## 12. Recorded Results

scenario_1_baseline_response.json

scenario_2_treatment_changed_response.json

scenario_3_hierarchy_changed_response.json

scenario_4_insufficient_evidence_response.json

These files contain actual saved model responses,
not manually fabricated demonstration results.
