# STACK.md — Confirmed tech stack

> Only Component A is confirmed from CLAUDE.md. B, C, D rows are placeholders — owners to fill in.

| Component | Language | API | Storage / Graph | Key libraries |
|---|---|---|---|---|
| A | Python 3.10+ | FastAPI + uvicorn (port 8000) | Neo4j (TREATED_BY etc.), SQLite index, JSON corpus | python-dotenv, neo4j driver |
| B | TBD | TBD (port 8001) | Reads A's Neo4j (read-only) | TBD |
| C | TBD | TBD (port 8002) | — | TBD |
| D | TBD | TBD (port 8003) | Reads A's Neo4j (read-only) | TBD |

Pipeline: `Query → D → B (via A's graph) → C → Brief`
