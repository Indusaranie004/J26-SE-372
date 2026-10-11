# Tech Stack — J26-SE-372
**AI Driven Law Document Analysis System for Sri Lankan Courts**

---

## Component A — Precedent Validity Knowledge Graph
*Kandewatta G.G.M.S | IT23297722*

| Technology | Purpose | Requirement |
|---|---|---|
| Python 3.10+ | Runtime | Required locally only to run Component A code — others just call the API |
| FastAPI + Uvicorn | REST API | Exposes all data through one interface |
| Neo4j AuraDB Free Tier | Knowledge graph | Cloud-hosted — no local installation needed |
| ChromaDB | Vector store | Self-hosted inside Component A container |
| SQLite + JSON files | Document store | Built-in Python — no installation |
| XLM-RoBERTa via HuggingFace | Bilingual NER | GPU needed only for fine-tuning (one month, Colab Pro). Inference runs on CPU |
| Render | API deployment | Component A API deployed here |
| Label Studio | Annotation | Browser-based, runs locally on port 8080 |
| GitHub (SC) + HuggingFace (CA, Acts) | Corpus source | Cloned and ingested once — not shared via repo |

---

## Component B — Graph-Aware Legal Precedent Retrieval Engine
*Kandaudahewa C.I. | IT23453142*

| Technology | Purpose | Requirement |
|---|---|---|
| Python 3.10+ | Runtime | Required locally only to run Component B code — others just call the API |
| sentence-transformers | BGE-M3 embeddings | GPU for fine-tuning (one-time, Colab). Inference on CPU |
| torch | ML framework | CPU build sufficient for inference |
| ChromaDB | Embedding store | Self-hosted inside Component B container — stores B's domain-adapted embeddings |
| rank-bm25 | Sparse retrieval | No additional service needed |
| HuggingFace datasets | Dataset loading | Used during fine-tuning pipeline only — no runtime dependency |
| neo4j (Python driver) | Graph queries | Read-only access to Component A's AuraDB URL — no local Neo4j installation |
| networkx | Graph utilities | Development and mock use only |
| numpy / pandas | Data handling | Built-in scientific computing — no external service |
| pydantic | Interface contracts | Defines D→B and B→C input/output contracts |
| FastAPI + Uvicorn | REST API | Component B API deployed here — others only need the endpoint |
| python-dotenv | Secrets management | AuraDB credentials and API keys in env vars — never hardcoded |

---

## Component C — Contextual Reasoning and Legal Brief Generator
*Dinuri Nureka A L D | IT23192478*

| Technology | Purpose | Requirement |
|---|---|---|
| Python 3.10+ | Runtime | Required locally only to run Component C code |
| LLM APIs — GPT-5, Gemini 2.5 Flash, Ministral 3 8B | LLM reasoning | Candidate LLMs tested comparatively with same controlled legal inputs. Requires provider API keys — no local GPU |
| OpenAI / Google / Mistral SDKs | LLM interface | Common model-adapter interface — LLM switchable without changing pipeline. API keys in env vars |
| HuggingFace Transformers + PEFT | Open-weight model testing | Used only if LoRA/QLoRA adaptation is tested. GPU access may be required |
| FastAPI + Uvicorn | REST API | Exposes reasoning and brief generation functions — others only need the endpoint |
| JSON / Pydantic | Data contracts | Defines input contract for precedent clusters and passages. Mock JSON usable during development |
| Structured prompting / context assembly in Python | Cross-case reasoning | No separate vector DB or retrieval engine inside Component C |
| Python evaluation scripts + pandas | Evaluation | Compares LLM outputs — citation correctness, unsupported-statement rate, faithfulness, latency |

---

## Component D — Intelligent Legal Issue Spotter & Argument Mapping Engine
*DE SILVA W.Y.S | IT23235038*

| Technology | Purpose | Requirement |
|---|---|---|
| Python 3.10+ | Runtime | Required locally only to run Component D code — others just call the API |
| FastAPI + Uvicorn | REST API | Exposes issue decomposition and citation strength prediction — others only need the endpoint and JSON schema |
| Llama-3-8B-Instruct via Groq API (Free) / Ollama | Issue tree generation | Groq bypasses local RAM limits, ultra-low latency (<1s). Ollama for offline fallback. Groq API key in env vars |
| XGBoost (via scikit-learn) | Citation strength prediction (SCSPM) | Lightweight tree-based model — runs entirely on local CPU |
| SHAP | Explainability metrics | Feature importance for every predicted citation strength score in argument map |
| Pandas / NumPy | Feature engineering and evaluation | RMSE, Pearson r for SCSPM evaluation |
| Pydantic / JSON | Data contracts | Defines Structured Issue Tree and Enriched Argument Map input/output contracts |
| Neo4j Python Driver | Graph queries | Read-only Cypher queries to fetch citation metadata from Component A — no local Neo4j needed |

---

## Shared Tools

| Tool | Purpose |
|---|---|
| Git + GitHub | Version control and PR reviews |
| MS Planner | Sprint task management |
| MS Teams | Communication and meeting notes |
| Render | API deployment for all components |
| Google Colab Pro | GPU training — fine-tuning only |