# Cherry FundOps integration

FundOps Agent Studio is deployed as a separate backend microservice. Cherry FundOps remains the
judge-facing control room and financial control authority.

## Input boundary

The end-user input contract lives in Cherry FundOps:

1. capital-call **PDF**;
2. commitment/control **Excel (.xlsx)**;
3. fund cash/bank **JSON**.

Cherry extracts and validates those sources, applies its strict deterministic controls and sends only
structured case data plus SHA-256 evidence hashes to this service.

## API

```text
GET  /integration/cherry/health
POST /integration/cherry/capital-call
```

`POST /integration/cherry/capital-call` performs:

- canonical capital-call construction with source provenance;
- `capital-call-review` agent execution;
- deterministic expected-vs-actual cash reconciliation;
- exception prioritisation through `exception-investigation`;
- analysis-only output back to Cherry.

Cherry retains the final `auto_reconcile`, `require_approval` or `request_evidence` control state.
Agent Studio cannot initiate or authorise a payment.

## Database

The service already uses PostgreSQL through `DATABASE_URL`. For deployment, reuse the existing
PostgreSQL/Cloud SQL **instance**, but point Agent Studio at a dedicated `fundops` database (or an
otherwise isolated database) on that instance. Do not connect Agent Studio directly to Cherry Money
application tables.

The existing Alembic migration creates the FundOps model-registry tables in that database.

## Cloud Run

Use `.github/workflows/deploy-cloudrun.yml`.

Required GitHub environment/repository variables:

```text
GCP_PROJECT_ID
GCP_WORKLOAD_IDENTITY_PROVIDER
GCP_DEPLOY_SERVICE_ACCOUNT
FUNDOPS_RUNTIME_SERVICE_ACCOUNT
FUNDOPS_DATABASE_SECRET
```

Optional:

```text
FUNDOPS_LLM_API_KEY_SECRET
FUNDOPS_LLM_MODEL
CHERRY_FINOPS_RUNTIME_SERVICE_ACCOUNT
```

`FUNDOPS_DATABASE_SECRET` is the name of an existing Google Secret Manager secret whose latest
version contains the SQLAlchemy PostgreSQL URL.

The workflow deploys `fundops-agent-studio` with `--no-allow-unauthenticated` and can grant the
Cherry FundOps runtime service account `roles/run.invoker`.

After deployment, configure Cherry with the returned service URL for both:

```text
FUNDOPS_STUDIO_API_URL
FUNDOPS_STUDIO_AUDIENCE
```

Cherry then obtains a Cloud Run IAM ID token automatically for each server-to-server call.
