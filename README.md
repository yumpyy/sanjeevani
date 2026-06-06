# Sanjeevani

> An AI healthcare assistant that triages general medical complaints
> and supports mental-health conversations through a stateful, multi-agent
> backend and a polished chat UI.

![Status: in active development](https://img.shields.io/badge/status-in%20active%20development-yellow)
![Frontend: Next.js 15](https://img.shields.io/badge/frontend-Next.js%2015-black)
![Backend: FastAPI + LangGraph](https://img.shields.io/badge/backend-FastAPI%20%2B%20LangGraph-009688)
![LLMs: Groq / Gemini / Ollama](https://img.shields.io/badge/LLMs-Groq%20%2F%20Gemini%20%2F%20Ollama-blue)
![Persistence: Postgres 16](https://img.shields.io/badge/persistence-Postgres%2016-336791)
![Tests: pytest passing](https://img.shields.io/badge/tests-pytest%20passing-brightgreen)

---

## What it does

Sanjeevani presents two front-doors to the user:

- **Physician** — a multi-turn triage that asks OLDCARTS-style
  clarifying questions, generates a structured prescription and
  SOAP note, and short-circuits to an emergency banner if red-flag
  symptoms are detected. Backed by a RAG pipeline that grounds its
  recommendations in NCBI PubMed and a local vector store.
- **Therapist** — an empathetic conversational agent with a closing
  self-care summary. Optionally paired with a HeyGen streaming avatar.

Both flows share the same Next.js chat shell and the same FastAPI
backend, routed by a real supervisor.

> The product is informational and educational only. It is **not** a
> substitute for professional medical advice, diagnosis, or treatment.

---

## Why it's interesting (for reviewers)

This codebase is a deliberately small, deliberately production-shaped
example of a stateful multi-agent system:

- **Real supervisor routing** — a `classify()` function picks the
  physician or therapist sub-graph at session start. The two sub-graphs
  share a Postgres checkpointer but are fully namespaced
  (`physician:<id>` vs `therapist:<id>`).
- **Deterministic graph termination** — the question loop has a
  hard max-turns guard (8 turns) and a short-circuit on emergency
  detection, so the graph cannot loop forever.
- **Persistent, resumable state** — every `/continue` call resumes
  the exact LangGraph thread; close the tab, come back tomorrow, the
  same doctor picks up where it left off.
- **Hard-fail at startup** — the API refuses to boot if Postgres is
  unreachable. No silent degradation to in-memory state.
- **Structured LLM output everywhere** — every node uses
  `llm.with_structured_output(<Pydantic model>)`, with a single
  `doctors/models.py` as the source of truth for shapes that cross
  the API boundary.
- **Tested end-to-end against real infra** — `tests/e2e_smoke.py`
  drives the live FastAPI process (stubbed LLM, real Postgres) for
  both the physician and therapist flows.
- **Clean code boundaries** — the legacy raw-LangChain implementation
  lives in `api/legacy/` and is not imported by the runtime. The
  tools layer (`api/agents/tools/`) is a thin set of LangChain
  `@tool` instances, swappable per LLM provider.

For a deep dive, see [`arch.md`](./arch.md).
For dev commands and conventions, see [`AGENTS.md`](./AGENTS.md).

## Agent flow at a glance

![Supervisor + sub-graph dispatch](api/assets/supervisor_flow.png)

The `classify()` function at the top routes each new session into the
physician or therapist sub-graph. Both sub-graphs are real LangGraph
state machines with Postgres-backed checkpoints; the supervisor itself
is intentionally not a graph (see `arch.md` for why).

| | Physician | Therapist |
|---|---|---|
| Flow | ![](api/assets/physician_graph.png) | ![](api/assets/therapist_graph.png) |
| `interrupt_after` | `collect_history` | `respond` |
| Termination | `soap_note_generated` or emergency | `recommended` |

---

## Quickstart

You need **Docker** (for Postgres), **Node 20+**, **Python 3.13+**,
and **uv** (or pip).

```bash
# 1. Postgres for the LangGraph checkpointer
docker compose up -d
docker compose ps   # wait for "healthy"

# 2. Backend
cd api
uv sync --extra dev
uv run fastapi dev main.py          # http://localhost:8000

# 3. Frontend (in a new terminal)
cd ..
npm install
npm run dev                          # http://localhost:3000
```

Set `LLM_PROVIDER=gemini` (or `groq`, or `ollama`) in `api/.env`. A
sample lives at `api/.env.example`.

---

## Tech stack

**Frontend** — Next.js 15 (App Router), React 19, TypeScript, Tailwind,
Framer Motion, shadcn/ui, HeyGen streaming avatar.

**Backend** — FastAPI, LangGraph 0.3, LangChain, Pydantic v2,
`langgraph-checkpoint-postgres`, `psycopg`, ChromaDB, NCBI E-utilities.

**Infra** — Postgres 16 (docker-compose), uv for Python deps.

---

## API surface (one-screen summary)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/doctors/` | List available doctor types |
| `POST` | `/diagnosis/{doctor_id}/` | Start a session, returns first question |
| `POST` | `/diagnosis/{session_id}/continue` | Send the user's answer |
| `GET` | `/diagnosis/{session_id}/history` | Q&A history |
| `GET` | `/diagnosis/{session_id}/recommendation` | Final prescription + SOAP note |
| `GET` | `/diagnosis/{session_id}/state` | Debug — raw state snapshot |
| `GET` | `/health` | Liveness |

Full request/response shapes are documented inline in `api/main.py`.

---

## Repository layout

```
.
├── app/                    Next.js App Router
├── components/             React components + shadcn/ui
├── lib/                    Frontend utilities
├── api/                    FastAPI + LangGraph backend
│   ├── main.py             Endpoints
│   ├── config.py           LLM, embeddings, checkpointer
│   ├── agents/             LangGraph state, sub-graphs, nodes, tools
│   ├── doctors/            Shared Pydantic schemas
│   ├── legacy/             Old implementation, kept for reference, not imported
│   ├── tests/              pytest unit tests + e2e smoke
│   └── utils/              Image analysis, web search helpers
├── arch.md                 Architecture deep-dive
├── AGENTS.md               Dev commands and code style
└── docker-compose.yml      Postgres for the checkpointer
```

---

## Running tests

```bash
cd api
uv run pytest                    # all unit tests
uv run pytest -k emergency       # just the emergency short-circuit
python tests/e2e_smoke.py        # end-to-end against a live API process
```

By default unit tests use `MemorySaver`. Set `POSTGRES_URL` to exercise
the real Postgres checkpointer path.

---

## What I'd show in a 15-minute interview

1. The supervisor + sub-graph split in `api/agents/supervisor.py`
   (15 lines of routing) plus the two compiled sub-graphs in
   `agents/physician_graph.py` and `agents/therapist_graph.py`.
2. The `interrupt_after` two-invoke pattern in `api/main.py:_continue`
   — the trickiest bit of glue code in the project.
3. The hard-fail Postgres wiring in `api/config.py` and
   `docker-compose.yml`.
4. The end-to-end smoke test in `api/tests/e2e_smoke.py` that
   drives both flows through a real API server and a real DB.
5. The Pydantic-only contract surface in `api/doctors/models.py`.

---

## License

MIT.
