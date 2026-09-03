# FundOps Agent Studio — Implementation Plan

## Product objective
Build a configurable agent platform for private-market fund operations. A fund manager describes a repetitive workflow in natural language and receives a governed, auditable agent assembled from reusable tools.

## Architecture principles
- LLMs handle intent understanding, semantic mapping, planning, exception explanation and natural-language interaction.
- Deterministic Python services handle arithmetic, reconciliation, tolerances, financial calculations and validation rules.
- Every material result must have evidence/lineage to its source workbook cell, JSON path or normalized record.
- Agents are declarative workflows rather than bespoke applications.
- Human approval is required before consequential external actions.
- Synthetic/anonymised data only for the hackathon repository.

---

## Phase 0 — Foundation & architecture — COMPLETE
Repository structure, architecture docs, FastAPI/React skeletons, environment config, Docker Compose, tests and package boundaries are in place.

## Phase 1 — Agent Runtime — COMPLETE
Reusable runtime is implemented with:
- agent/request/workflow models;
- planner abstraction with static planner;
- allow-listed tool registry and tool metadata;
- retry policy and linear backoff;
- per-step timeout boundary;
- structured run state and in-memory persistence boundary;
- lifecycle events and event history;
- validation hooks;
- FastAPI APIs for tools, agents and runs;
- tests for execution, failures, retries, events and API flow;
- declarative demo agent and smoke script.

Lifecycle:
`RECEIVE → UNDERSTAND → PLAN → EXECUTE → VALIDATE → EXPLAIN → COMPLETE`

## Phase 2 — Configurable Canonical Fund Data Model — COMPLETE
Implemented as metadata rather than hard-coded entity classes:
- versioned `FundModelDefinition`, entities, fields and relationships;
- PostgreSQL persistence for models, versions, entities, fields and relationships;
- Alembic migration `0001_fund_model_registry`;
- schema registry REST APIs and activation lifecycle;
- canonical record envelope with provenance/evidence;
- JSON Schema generation;
- record validation against an exact model version;
- schema diff with compatibility/risk classification;
- reviewable migration-plan generation (no silent data mutation);
- tenant/client overlay composition with base-model lineage;
- unit tests for schema generation, breaking changes and overlays.

Key rule: **active model versions are never edited in place**. Changes create a new version and require review before activation.

## Phase 3 — Data Ingestion & Schema Mapping
Excel/JSON readers, table/header detection, type inference, normalization, schema mapping, entity matching and lineage.

## Phase 4 — Deterministic Reconciliation Engine
Exact/fuzzy matching, amount/date/currency checks, tolerances, missing/duplicate detection, sign and aggregation checks, reason codes and evidence.

## Phase 5 — Fund Reconciliation Agent
Upload → schema detection → mapping → normalization → reconciliation → financial validation → materiality ranking → explanation → evidence-backed report/export.

## Phase 6 — Agent Factory
Natural language → intent/domain/inputs → workflow generation → tool selection → workflow validation → human review → publish. Generated workflows remain declarative YAML/JSON and execute only registered tools.

## Phase 7 — Fund Operations Agent Library
Reconciliation, Excel quality/risk, capital calls, NAV, valuation review, normalization, portfolio exposure, investor reporting, exception investigation and fund-data Q&A.

## Phase 8 — Evidence, Audit & Human-in-the-Loop
Source references, evidence bundles, execution history, workflow/agent versions, decision logs, confidence, approvals and snapshots.

## Phase 9 — Agent Studio UI
Dashboard, Agent Builder and Run Detail. Hackathon priority: upload → describe → execute → review exceptions → inspect evidence → export.

## Phase 10 — LLM Optimization, Evaluation & Guardrails
Prompt/version management, structured outputs, model routing, token/cost tracking, cached mappings, eval datasets, golden tests, hallucination/numeric checks and prompt-injection defenses.

## Phase 11 — Deployment & Security
React → FastAPI → Agent Runtime → PostgreSQL → Object Storage. Later add SSO/RBAC/tenant isolation/encryption/secrets/rate limits/observability/CI/CD/backups. Avoid premature Kafka/Kubernetes/microservices.

## Phase 12 — Hackathon Demo & Investor Readiness
Demonstrate a realistic reconciliation workflow, evidence-backed exceptions, export, and generation of a second agent through Agent Factory. Track time saved, exceptions detected, accuracy, evidence coverage, agent creation time and LLM cost.

## Recommended hackathon scope
**Minimum compelling product: Phases 0–6 + a thin slice of 8–9.**
