
# Function 2 — PP1 Experiment Summary

## Component C: Contextual Reasoning and Legal Brief Generation

### 1. Objective

Function 2 aims to generate structured, evidence-referenced
legal research briefs using original case evidence and
contextual reasoning produced by Function 1.

The PP1 implementation focuses on:

- Structured legal research brief generation
- Claim-level evidence references
- Judicial-treatment metadata citations
- Reference-grounding validation
- Human-readable legal brief formatting
- Claim-to-source evidence auditing
- Handling insufficient legal evidence

All recorded experiments use fictional legal data.

### 2. Implementation

The legal brief pipeline consists of:

1. BriefGenerationRequest validation
2. Legal evidence and reasoning context preparation
3. Gemini-based structured legal brief generation
4. Pydantic output validation
5. Claim-reference grounding validation
6. Human-readable Markdown formatting
7. Claim-to-evidence audit reporting

The generated brief contains relevant facts, legislation,
precedents, judicial treatment, legal analysis, arguments,
counterarguments, application to facts, conclusion,
and limitations.

### 3. Experiment A: Baseline Legal Brief Generation

Scenario:

A fictional public authority revoked a business permit
without prior notice or an opportunity to respond.

The supplied evidence included three fictional precedents,
five case facts, and relevant fictional legislation.

Observed results:

- Legal claims: 23
- Evidence references: 39
- Unresolved source references: 0
- Claims flagged by the evidence audit: 6

All six review flags involved statements discussing
judicial treatment without citing judicial-treatment
metadata.

The baseline output was generated before introducing
dedicated judicial-treatment references.

### 4. Experiment B: Improved Citation Traceability

The implementation was extended with a dedicated
judicial_treatment evidence-reference type.

The reference includes the treating source case,
treated target case, treatment status, and optional
effective date and scope.

An additional live legal brief was generated using
the same fictional scenario.

Observed results:

| Metric | Original | Improved |
|---|---:|---:|
| Legal claims | 23 | 23 |
| Evidence references | 39 | 39 |
| Unresolved references | 0 | 0 |
| Claims flagged for review | 6 | 0 |

The improved output used judicial-treatment references
and triggered no review flags under the current audit rules.

Interpretation:

This experiment demonstrates improved citation
traceability in the tested scenario.

The two outputs were separate Gemini generations.
Consequently, the results do not isolate the effect
of the citation change under a controlled experiment.

The reduction in review flags must not be interpreted
as a measured reduction in hallucinations or as proof
of complete legal accuracy.

### 5. Experiment C: Insufficient Evidence

Scenario:

The fictional business requested financial compensation
for lost income after the permit revocation.

The supplied authorities addressed procedural fairness
but did not establish a financial compensation remedy.

Observed results:

- Legal claims: 24
- Evidence references: 35
- Unresolved references: 0
- Claims flagged by the evidence audit: 0
- Conclusion claims marked insufficient_evidence: 1
- Recorded limitations: 3

The generated conclusion acknowledged that the supplied
authorities did not establish entitlement to financial
compensation for lost income.

The model distinguished supported procedural principles
from the unresolved compensation question.

This demonstrates appropriate uncertainty handling in
the recorded scenario, but does not establish reliability
across other legal problems.

### 6. Evidence Grounding and Auditing

The grounding validator checks:

- Case and passage identifier validity
- Passage ownership
- Supplied legislation identifiers and sections
- Original case fact indices
- Directional judicial-treatment metadata
- Optional judicial-treatment date and scope

The evidence audit also displays original source text
beside generated claims and identifies certain citation
issues for manual review.

A resolved source reference does not necessarily imply
that the cited evidence supports the complete claim.

Support statuses are assigned by the generating model
and must not be treated as independent verification.

### 7. API Demonstration

Function 2 is exposed through FastAPI:

- GET /api/brief/demo/recorded
- GET /api/brief/demo/readable
- POST /api/brief/generate

The recorded endpoints provide demonstrations without
calling Gemini.

The POST endpoint generates a new legal research brief
using the supplied evidence and Function 1 reasoning.

Live generation was successfully tested through HTTP,
returning status 200.

### 8. Automated Testing

The current complete Component C test suite contains
146 passing tests.

The suite covers Function 1 compatibility and Function 2
data models, context preparation, generation services,
grounding, judicial-treatment references, formatting,
API behavior, and evidence auditing.

Passing tests establish the tested software behavior,
not independent legal correctness.

### 9. Limitations

The current prototype has the following limitations:

- Experiments use fictional development evidence.
- Automatic semantic entailment verification is not
  implemented.
- The audit uses reference resolution and targeted
  review heuristics.
- Upstream judicial-treatment metadata is not
  independently verified against published judgments.
- Legal hierarchy and statutory interpretation still
  require domain-expert review.
- The improved output is one observed generation rather
  than evidence of statistically reliable performance.
- Integration with the other research components remains
  dependent on agreed production interfaces.

### 10. Future Work

Future work includes:

- Expert-reviewed claim-to-evidence evaluation
- Testing with appropriately sourced real judgments
- Broader experiments with conflicting authorities
- Quantitative grounding and citation-quality metrics
- Improved detection of unsupported legal propositions
- Integration with upstream retrieval and knowledge
  engineering components
- Additional document export and presentation features

### 11. PP1 Conclusion

Function 2 has demonstrated operational structured legal
brief generation, reference-grounding validation, citation
traceability, and evidence-limited conclusions on
fictional development scenarios.

The PP1 prototype provides a working foundation for
subsequent evaluation, integration, and refinement.

It is not yet a legally validated or production-ready
drafting system.
