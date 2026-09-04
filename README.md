# FundOps Agent Studio

> **An AI-powered control layer between spreadsheets and fund-management systems.**

FundOps Agent Studio is a configurable agent platform for private-market fund operations. It turns repetitive Excel, JSON and document-driven workflows into governed, auditable AI workflows.

## Product vision

Fund managers should be able to describe an operational task in plain English and get a reusable agent that can ingest fund data, map schemas, run deterministic financial checks, identify exceptions, explain findings and produce evidence-backed outputs.

### Core principles

- **LLM for reasoning, not arithmetic** — LangChain handles natural-language planning and explanation; financial calculations and validation remain deterministic.
- **Evidence first** — every material finding should trace back to a source file, sheet/cell or JSON path.
- **Human-in-the-loop** — material exceptions and consequential actions can require approval.
- **Configuration over custom code** — agents are workflows assembled from reusable tools.
- **Schema-aware data** — heterogeneous fund data is mapped into a canonical model.
- **Auditability** — retain inputs, mappings, rules, execution state, evidence and outputs.

## MVP

The first production slice is the **Fund Reconciliation Agent**:

1. Upload independent administrator and fund-manager Excel/JSON data.
2. Inspect and map each source independently.
3. Normalize entities, dates, currencies and amounts.
4. Reconcile records and aggregates with configurable tolerances.
5. Rank material exceptions.
6. Explain findings with source evidence.
7. Expose audit and approval state.

## Phase 10 — LLM layer

The Agent Studio now supports an optional LangChain-backed LLM planner:

```text
User request
     |
 LangChain LLM
     |  structured plan
     v
Allow-listed Tool Registry
     |
Deterministic Agent Runtime
     |
Financial controls / evidence / audit
     |
Human approval before publication
```

Endpoints:

- `GET /agent-factory/llm/status`
- `POST /agent-factory/draft-llm`
- `POST /agent-factory/explain`

The LLM cannot invent tools, execute financial calculations, bypass deterministic validation or publish an agent. See [`docs/PHASE_10_LLM.md`](docs/PHASE_10_LLM.md).

## Architecture

```text
React / Agent Studio UI
          |
       FastAPI
          |
   Agent Factory
  LLM intent -> structured plan
          |
    Agent Runtime
 plan -> execute -> validate -> explain
          |
      Tool Registry
 /       |       |        \
Excel   JSON  Reconcile   Validation
          |       |           \
          +---- Fund Data ----+
                    |
              PostgreSQL
                    |
          Evidence / Audit Trail
```

## Repository structure

```text
backend/          FastAPI API and application services
frontend/         Agent Studio web UI
agents/           Agent definitions and templates
tools/            Reusable deterministic tools
fund_model/       Canonical private-markets data model
workflows/        Declarative agent workflows
sample_data/      Synthetic/demo fund data
docs/             Architecture and implementation documentation
tests/            Cross-component tests
```

## Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health endpoint:

```text
GET http://localhost:8000/health
```

### Configure LLM planning

```text
LLM_PROVIDER=openai
LLM_MODEL=<model-name>
LLM_API_KEY=<provider-key>
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
```

The application does not require an LLM key to start; deterministic workflows remain available when LLM configuration is absent.

### Docker

```bash
docker compose up
```

## Roadmap

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the complete Phase 0–12 plan. Phase 10 LLM planning, explanation, guardrails and evaluation scaffolding are implemented; remaining work is deployment/security hardening and final hackathon/demo polish.
