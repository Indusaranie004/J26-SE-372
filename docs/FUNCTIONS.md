# PP1 Function Contracts — All Components
**Group J26-SE-372 | AI Driven Law Document Analysis System for Sri Lankan Courts**

---

## Component A — Kandewatta G.G.M.S | IT23297722

### Function 1 — Bilingual Legal Entity Extraction Pipeline

| Field | Detail |
|---|---|
| **Input** | Raw Supreme Court judgment text (string) |
| **Processing** | Segments text into caption, header, body and conclusion sections with character offsets → extracts named entities (Case Number, Judge, Counsel, Party, Act, Citation) using rule-based NER |
| **Output** | Structured JSON record saved to document store and indexed in SQLite |
| **Depends on** | None — fully self-contained |
| **Others depend on this** | Component B needs case entities for seed filtering; Component C needs section text for evidence grounding; Component D needs entities for issue tree |

### Function 2 — Treatment Triple Extraction and Neo4j Graph Population

| Field | Detail |
|---|---|
| **Input** | Structured JSON from Function 1 |
| **Processing** | Identifies citation contexts in body section → classifies each as followed / distinguished / overruled / doubted using keyword classifier with procedural noise filtering → binds treating case and treated case using direction-aware attribution → writes typed TREATED_BY edges with treatment type, effective date, evidence snippet and character offset into Neo4j using MERGE |
| **Output** | Neo4j graph updated with TREATED_BY, DECIDED_BY, INVOLVES_ACT, APPEALED_FROM edges |
| **Depends on** | Function 1 output |
| **Others depend on this** | Component B's expand stage traverses TREATED_BY edges; Component D's SCSPM trains on treatment type signals from these edges |

---

## Component B — Kandaudahewa C.I. | IT23453142

### Function 1 — Concurrent Hybrid Retrieval

| Field | Detail |
|---|---|
| **Input** | Raw parsed legal documents — precedent text and metadata stored in document store from Component A |
| **Processing** | BM25 sparse retrieval and BGE-M3 dense retrieval running concurrently, merged with Reciprocal Rank Fusion |
| **Output** | Ranked list of relevant precedents with scores |
| **Depends on** | Component A's document store — precedent text and metadata |
| **Others depend on this** | Component C's reasoning function receives ranked precedent clusters from this function |

### Function 2 — Relationship-Aware Graph Traversal

| Field | Detail |
|---|---|
| **Input** | Seed precedents from Function 1 + Component A's populated Neo4j graph |
| **Processing** | Traverses Neo4j knowledge graph with typed edges — CITES, GOVERNED_BY, APPEAL_OF — to expand the precedent cluster with related authorities |
| **Output** | Enriched precedent cluster with relational context at triplet-level granularity |
| **Depends on** | Component A's Neo4j graph with typed edges — CITES, GOVERNED_BY, APPEAL_OF |
| **Others depend on this** | Component C receives this enriched cluster as input to reasoning |

---

## Component C — Dinuri Nureka A L D | IT23192478

### Function 1 — Cross-Case Contextual & Precedent-Aware Reasoning

| Field | Detail |
|---|---|
| **Input** | Ranked precedent clusters and relevant passages from Component B |
| **Processing** | Synthesises multiple retrieved precedents using facts, legal principles, court hierarchy, chronology, legislation and judicial-treatment metadata (followed, distinguished, overruled) |
| **Output** | Structured reasoning output with cross-case analysis |
| **Depends on** | Component B's precedent retrieval function for ranked clusters and passages. Component A's knowledge graph for court hierarchy metadata, legislation links, litigation history and judicial-treatment information. *For PP1: mock/manually prepared precedent clusters can be used using the agreed input structure, then replaced with actual A/B outputs during integration* |
| **Others depend on this** | Component C's Function 2 receives this reasoning output |

### Function 2 — Evidence-Grounded Legal Brief Generation

| Field | Detail |
|---|---|
| **Input** | Reasoning output from Function 1 + source passages |
| **Processing** | Maps generated legal claims to retrieved source passages → creates evidence-to-conclusion trace → generates structured legal brief only from grounded analysis |
| **Output** | Structured legal brief with citation evidence and source grounding |
| **Depends on** | Component B's passage-level retrieval function for source passages. Indirectly uses legal metadata from Component A through the reasoning output. *For PP1: same mock precedent/passages dataset can be used initially* |
| **Others depend on this** | Final output consumed by the user interface |

---

## Component D — DE SILVA W.Y.S | IT23235038

### Function 1 — Legal Issue Spotting & Issue Tree Generation

| Field | Detail |
|---|---|
| **Input** | Lawyer's raw natural language description of a client's problem |
| **Processing** | Identifies core legal claims (propositions) → breaks problem into structured hierarchy of specific legal sub-issues, required legal elements and missing factual contexts using LLM-based decomposition pipeline (Llama-3-8B via Groq) |
| **Output** | Structured issue tree defining exactly what legal questions need to be researched |
| **Depends on** | None — no upstream component dependency |
| **Others depend on this** | Component D's Function 2 takes this issue tree as input; Component B uses decomposed sub-queries for retrieval |

### Function 2 — Argument Map Generation with Citation Strength Prediction

| Field | Detail |
|---|---|
| **Input** | Structured issue tree from Function 1 |
| **Processing** | Maps each legal sub-issue to relevant supporting and opposing authorities → evaluates reliability of those authorities using trained XGBoost SCSPM model → assigns real-time citation strength scores and SHAP explainability metrics to each authority |
| **Output** | Enriched argument map with citation strength scores and explainability metrics per authority |
| **Depends on** | Component A's Knowledge Graph for citation metadata — court hierarchy, judicial treatment dates. *For PP1: mock metadata can be used initially using the agreed input structure, then replaced with actual Component A outputs during integration* |
| **Others depend on this** | Component B uses the structured sub-queries and authority map to guide retrieval |