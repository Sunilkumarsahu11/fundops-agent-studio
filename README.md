# FundOps Agent Studio

> **A deterministic private-markets agent runtime that can sit behind Cherry FundOps.**

FundOps Agent Studio is a configurable agent platform for private-market fund operations. It turns repetitive Excel, JSON and document-driven workflows into governed, auditable workflows while keeping financial calculations inside deterministic tools.

## Cherry FundOps integration

For the Ylookup × Encode product flow, the two repositories stay separate and communicate over a backend API:

```text
User / judge
    |
    |  PDF + Excel + JSON
    v
Cherry FundOps
    |
    |  PDF extraction + strict controls
    |  structured case + SHA-256 source hashes
    v
FundOps Agent Studio
    |
    |  capital-call review
    |  canonical records / provenance
    |  fund reconciliation
    |  exception investigation
    v
Cherry FundOps control room
```

Cherry is the user-facing orchestrator and remains the financial-control authority. Agent Studio is an analysis microservice and does not initiate or authorise payments.

### Integration API

```text
GET  /integration/cherry/health
POST /integration/cherry/capital-call
```

The raw evidence contract is owned by Cherry FundOps and is exactly:

- capital-call **PDF**;
- commitment/control **Excel (.xlsx)**;
- fund cash/bank **JSON**.

Agent Studio receives structured records derived from those inputs rather than receiving the original raw files. Source file names and SHA-256 hashes are preserved as provenance.

## Product vision

Fund managers should be able to describe an operational task in plain English and get a reusable agent that can ingest fund data, map schemas, run deterministic financial checks, identify exceptions, explain findings and produce evidence-backed outputs.

### Core principles

- **LLM for reasoning, not arithmetic** — LangChain handles natural-language planning and explanation; financial calculations and validation remain deterministic.
- **Evidence first** — every material finding should trace back to a source file, sheet/cell or JSON path.
- **Human-in-the-loop** — material exceptions and consequential actions can require approval.
- **Configuration over custom code** — agents are workflows assembled from reusable tools.
- **Schema-aware data** — heterogeneous fund data is mapped into a canonical model.
- **Auditability** — retain inputs, mappings, rules, execution state, evidence and outputs.

## Agent catalogue

The reusable FundOps library includes:

- fund reconciliation;
- Excel quality review;
- capital-call review;
- NAV review;
- valuation review;
- normalization;
- portfolio exposure;
- investor reporting;
- exception investigation;
- fund-data Q&A.

## LLM layer

The Agent Studio supports an optional LangChain/OpenAI Responses API planning and explanation layer:

```text
User request
     |
     v
Structured LLM plan
     |
     v
Allow-listed Tool Registry
     |
     v
Deterministic Agent Runtime
     |
     v
Financial controls / evidence
     |
     v
Human approval where required
```

Endpoints:

- `GET /agent-factory/llm/status`
- `POST /agent-factory/draft-llm`
- `POST /agent-factory/explain`

The LLM cannot invent tools, execute financial calculations, bypass deterministic validation or publish an agent.

## Architecture

```text
Cherry FundOps / optional React UI
              |
           FastAPI
              |
       FundOps agent library
              |
       Deterministic runtime
              |
   Reconciliation / review tools
              |
       Canonical fund model
              |
     SQLAlchemy + Alembic
              |
    PostgreSQL or MySQL
```

## Database

The persistence layer uses SQLAlchemy and Alembic. `DATABASE_URL` may point at PostgreSQL or MySQL.

Examples:

```env
# PostgreSQL
DATABASE_URL=postgresql+psycopg://fundops:password@host:5432/fundops

# MySQL / existing Cherry database infrastructure
DATABASE_URL=mysql+pymysql://fundops:password@host:3306/fundops_agent
```

When sharing the same database server/infrastructure as Cherry Money, give Agent Studio its **own database/schema/table ownership**. Do not point it at Cherry Money business tables and do not make it a second writer to Cherry accounting data.

Current Alembic-managed FundOps tables include the versioned fund-model registry (`fund_models`, `fund_model_versions`, `entity_definitions`, `field_definitions`, and `relationship_definitions`). Runtime/governance state remains suitable for hackathon/demo use; Cherry FundOps remains the authoritative audit/control boundary for the integrated flow.

## Repository structure

```text
backend/          FastAPI API and application services
frontend/         Agent Studio web UI (not required by Cherry integration)
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

Health endpoints:

```text
GET http://localhost:8000/health
GET http://localhost:8000/integration/cherry/health
```

### Configure optional LLM planning

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

## Cloud Run microservice deployment

`.github/workflows/deploy-cloudrun.yml` builds only the backend and deploys it as a private Cloud Run service. The workflow expects a Secret Manager secret containing `DATABASE_URL` and can grant the Cherry FundOps runtime service account `roles/run.invoker`.

The deployed service should not be public. Cherry FundOps supports Cloud Run service-to-service identity tokens via `FUNDOPS_STUDIO_API_URL` and `FUNDOPS_STUDIO_AUDIENCE`.

## Roadmap

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the broader implementation plan. For the hackathon integration, prioritize one validated user problem and keep the Agent Studio microservice behind the simple Cherry FundOps user experience.
