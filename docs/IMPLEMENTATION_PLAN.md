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
Implemented:
- reusable `FundAgentSpec`, `AgentInput` and `AgentOutput` contracts;
- catalog of 10 FundOps agents: reconciliation, Excel quality, capital-call review, NAV review, valuation review, normalization, portfolio exposure, investor reporting, exception investigation and fund-data Q&A;
- governed `FundOperationsLibrary` execution facade;
- fully enabled deterministic reconciliation agent backed by Phase 4/5 controls;
- exception investigation projection that preserves supplied deterministic exceptions;
- record-based Fund Data Q&A with source evidence and no fabrication of missing records;
- explicit `not_implemented` status for catalogued domain agents whose specialized workflow is deferred rather than using unsafe fallbacks;
- FastAPI catalog/detail/run endpoints under `/fund-ops`;
- automated catalog, reconciliation/evidence and Q&A tests;
- Phase 7 documentation.

Key rule: **the library is capability-driven. Catalogued agents cannot silently execute arbitrary logic; financial controls remain deterministic and evidence-backed.**

## Phase 8 — Evidence, Audit & Human-in-the-Loop — COMPLETE
Implemented:
- governed audit event capture for agent execution;
- immutable run snapshots containing the request, agent version, status and output;
- evidence extraction from canonical provenance and run output;
- approval lifecycle with pending, approved and rejected states;
- explicit actor/decision/reason fields for human approvals;
- audit and evidence APIs under `/governance`;
- approval APIs for consequential workflow decisions;
- tests covering audit capture, evidence and approval transitions;
- Phase 8 governance documentation.

Key rule: **material financial outcomes remain deterministic, evidence-backed and reviewable; human approval is explicit and never inferred from an LLM response.**

## Phase 9 — Agent Studio UI — IN PROGRESS
Implemented the first hackathon-ready workspace slice:
- agent library connected to `/fund-ops/agents`;
- natural-language task composer;
- selected-agent/version display;
- workflow execution against the backend;
- run status/result panel;
- responsive desktop/mobile layout;
- visual treatment for deterministic controls and evidence/audit readiness.

Remaining Phase 9 work:
- real Excel/JSON file upload wired to `/ingestion/run`;
- ingestion mapping/review screen;
- reconciliation configuration and exception table;
- run detail with audit timeline and evidence drill-down;
- approval controls;
- export report action.

## Phase 10 — LLM Optimization, Evaluation & Guardrails
Prompt/version management, structured outputs, model routing, token/cost tracking, cached mappings, eval datasets, golden tests, hallucination/numeric checks and prompt-injection defenses.

## Phase 11 — Deployment & Security
React → FastAPI → Agent Runtime → PostgreSQL → Object Storage. Later add SSO/RBAC/tenant isolation/encryption/secrets/rate limits/observability/CI/CD/backups. Avoid premature Kafka/Kubernetes/microservices.

## Phase 12 — Hackathon Demo & Investor Readiness
Demonstrate a realistic reconciliation workflow, evidence-backed exceptions, export, and generation of a second agent through Agent Factory. Track time saved, exceptions detected, accuracy, evidence coverage, agent creation time and LLM cost.

## Recommended hackathon scope
**Minimum compelling product: Phases 0–8 + the thin slice of Phase 9 currently implemented.**
