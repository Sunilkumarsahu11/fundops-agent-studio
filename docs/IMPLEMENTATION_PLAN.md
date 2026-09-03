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
Reusable runtime is implemented with agent/request/workflow models, planner abstraction, allow-listed tools, retries, timeouts, structured run state, lifecycle events, validation hooks, APIs and tests.

## Phase 2 — Configurable Canonical Fund Data Model — COMPLETE
Implemented versioned metadata-driven fund models, PostgreSQL persistence, schema registry APIs, canonical records with provenance, JSON Schema generation, validation, schema diff, migration plans and tenant overlays.

## Phase 3 — Data Ingestion & Schema Mapping — COMPLETE
Implemented Excel/JSON ingestion, source discovery, deterministic type inference, mapping candidates, unmapped-field reporting, normalization, canonical records and workbook/JSON provenance.

## Phase 4 — Deterministic Reconciliation Engine — COMPLETE
Implemented deterministic composite-key matching, duplicate/missing detection, amount/date/currency controls, tolerances, materiality, reason codes, evidence and reconciliation reporting.

## Phase 5 — Fund Reconciliation Agent — COMPLETE
Implemented reusable orchestration around the deterministic reconciliation engine, evidence-backed exception reports, materiality preservation and API endpoints.

## Phase 6 — Agent Factory — COMPLETE
Implemented natural-language request → declarative blueprint → tool selection → validation → human approval → published Agent Runtime definition, with starter templates and APIs.

## Phase 7 — Fund Operations Agent Library — COMPLETE
Implemented reusable contracts, a 10-agent catalog, governed execution facade, deterministic reconciliation, exception investigation, Fund Data Q&A, explicit `not_implemented` handling for deferred specialist workflows, APIs, tests and documentation.

Key rule: **the library is capability-driven. Catalogued agents cannot silently execute arbitrary logic; financial controls remain deterministic and evidence-backed.**

## Phase 8 — Evidence, Audit & Human-in-the-Loop — COMPLETE
Implemented:
- append-only audit event projection tied to agent runs and actors;
- run snapshots capturing request, output, status and agent version;
- evidence items linked to run/record provenance including source file, sheet, cell, JSON path and source field;
- automatic governance capture after runtime API execution;
- approval request/decision lifecycle with pending/approved/rejected states;
- prevention of approval decisions without a run snapshot and prevention of double decisions;
- governance APIs for audit, evidence, snapshots and approvals;
- automated governance tests and documentation.

Persistence remains an explicit in-memory boundary for this phase; the API contracts are ready for a durable PostgreSQL governance adapter.

## Phase 9 — Agent Studio UI
Dashboard, Agent Builder and Run Detail. Hackathon priority: upload → describe → execute → review exceptions → inspect evidence → export.

## Phase 10 — LLM Optimization, Evaluation & Guardrails
Prompt/version management, structured outputs, model routing, token/cost tracking, cached mappings, eval datasets, golden tests, hallucination/numeric checks and prompt-injection defenses.

## Phase 11 — Deployment & Security
React → FastAPI → Agent Runtime → PostgreSQL → Object Storage. Later add SSO/RBAC/tenant isolation/encryption/secrets/rate limits/observability/CI/CD/backups. Avoid premature Kafka/Kubernetes/microservices.

## Phase 12 — Hackathon Demo & Investor Readiness
Demonstrate a realistic reconciliation workflow, evidence-backed exceptions, export, and generation of a second agent through Agent Factory. Track time saved, exceptions detected, accuracy, evidence coverage, agent creation time and LLM cost.

## Recommended hackathon scope
**Minimum compelling product: Phases 0–8 + a thin slice of 9.**
