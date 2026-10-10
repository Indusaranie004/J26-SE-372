# Function Contracts

Pipeline: `Query → D → B (via A's graph) → C → Brief`

## Component A — Precedent Validity Knowledge Graph
| Module | Responsibility |
|---|---|
| `extraction/segmentation.py` | Section segmentation (caption/header/body/conclusion) |
| `extraction/entity_extractor.py` | Rule-based NER, 6 entity types |
| `extraction/document_store.py` | JSON writer + SQLite indexer |
| `extraction/treatment_extractor.py` | Treatment classification + direction attribution |
| `extraction/neo4j_writer.py` | Neo4j MERGE operations |
| `agent/validity_agent.py` | Natural language → Neo4j validity query |

## Component B — Graph-Aware Retrieval (TBD)
Stages: seed → expand (traverses `TREATED_BY`) → passage. Input: issues from D. Output: ranked precedent clusters for C.

## Component C — Reasoning & Brief Generator (TBD)
Input: ranked precedent clusters from B. Uses A's `/cases/{doc_id}/sections/{name}` for evidence grounding. Output: legal brief.

## Component D — Issue Spotter & Argument Mapping (TBD)
Stages: decomposition, citation_strength (SCSPM, trained on A's citation metadata), argument_mapping. Output: legal issues passed to B.

> B, C, D signatures to be added by their owners.
