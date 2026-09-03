# FundOps Agent Studio

> **An AI-powered control layer between spreadsheets and fund-management systems.**

FundOps Agent Studio is a configurable agent platform for private-market fund operations. It turns repetitive Excel, JSON and document-driven workflows into governed, auditable AI workflows.

## Product vision

Fund managers should be able to describe an operational task in plain English and get a reusable agent that can ingest fund data, map schemas, run deterministic financial checks, identify exceptions, explain findings and produce evidence-backed outputs.

### Core principles

- **LLM for reasoning, not arithmetic** — financial calculations and validation are deterministic.
- **Evidence first** — every material finding should trace back to a source file, sheet/cell or JSON path.
- **Human-in-the-loop** — material exceptions and consequential actions can require approval.
- **Configuration over custom code** — agents are workflows assembled from reusable tools.
- **Schema-aware data** — heterogeneous fund data is mapped into a canonical model.
- **Auditability** — retain inputs, mappings, rules, execution state, evidence and outputs.

## MVP

The first production slice is the **Fund Reconciliation Agent**:

1. Upload Excel and JSON fund data.
2. Detect and map source schemas.
3. Normalize entities, dates, currencies and amounts.
4. Reconcile records and aggregates with configurable tolerances.
5. Rank material exceptions.
6. Explain each exception with source evidence.
7. Export a reconciliation report.

## Architecture

```text
React / Agent Studio UI
          |
       FastAPI
          |
   Agent Factory
  intent -> plan -> workflow
          |
    Agent Runtime
 plan -> execute -> validate -> explain
          |
      Tool Registry
  /       |        |        \
Excel    JSON   Reconcile   Validation
          |       /           \
          +------ Fund Data ---+
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

### Docker

```bash
docker compose up
```

## Roadmap

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the complete Phase 0–12 plan.

The hackathon target is to complete the foundation through the Agent Factory and demonstrate a thin, polished slice of evidence/audit and the Agent Studio UI.
