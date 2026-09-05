# FundOps Agent Studio

> **A deterministic private-markets agent runtime designed to be consolidated into Cherry FundOps.**

FundOps Agent Studio is a configurable agent platform for private-market fund operations. It turns repetitive Excel, JSON and document-driven workflows into governed, auditable workflows while keeping financial calculations inside deterministic tools.

## Cherry FundOps integration

For the Ylookup × Encode product flow, the current integration is:

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

Cherry is the user-facing orchestrator and remains the financial-control authority. Agent Studio is analysis-only and does not initiate or authorise payments.

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

## Database: MySQL only

FundOps Agent Studio has been converted from PostgreSQL to **MySQL 8** so it can share the same database infrastructure as Cherry Money.

Example:

```env
DATABASE_URL=mysql+pymysql://fundops:password@mysql-host:3306/cherrybank?charset=utf8mb4
```

FundOps does not write to Cherry accounting tables. Its own tables are namespaced inside the same MySQL database:

```text
fundops_alembic_version
fundops_models
fundops_model_versions
fundops_entity_definitions
fundops_field_definitions
fundops_relationship_definitions
```

This gives us one MySQL database while maintaining clear table ownership and avoiding collisions with Laravel migrations.

## Target end-state: one database, one repo

The temporary two-repository integration is intentionally a transition state. The target is:

```text
cherry-agentic-finops
    |
    +-- Cherry PDF / Excel / JSON ingestion
    +-- strict deterministic controls
    +-- FundOps agent library
    +-- reconciliation / exception investigation
    +-- audit / evidence layer
    |
    v
Shared Cherry MySQL database
```

Once the MySQL conversion is proven green, the reusable Agent Studio backend modules can be moved into `sohamtech-uk/cherry-agentic-finops`. At that point the HTTP hop between the two repos can be removed and this repository can be archived as the historical source build.

## Product principles

- **LLM for reasoning, not arithmetic** — natural-language planning and explanation are optional; financial calculations and validation remain deterministic.
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
           MySQL 8
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

### Optional LLM planning

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

The local stack now starts MySQL 8, applies the namespaced FundOps Alembic migration and starts the backend.

## Cloud Run deployment

`.github/workflows/deploy-cloudrun.yml` builds only the backend and deploys it as a private Cloud Run service. `FUNDOPS_DATABASE_SECRET` should contain a MySQL `DATABASE_URL` pointing at the shared Cherry database. The service should remain private while the two-repository transition exists.

## Consolidation rule

Do not build new permanent functionality in both repos. Until consolidation is complete:

- Cherry owns raw PDF + Excel + JSON ingestion and financial-control outcomes.
- Agent Studio owns reusable analysis-agent code.
- MySQL is the shared database engine.
- New Agent Studio tables must use the `fundops_` prefix.

The final consolidation target is `sohamtech-uk/cherry-agentic-finops` as the single runtime repository.
