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
Implemented the 10-agent FundOps catalogue and deterministic shared-tool execution facade covering reconciliation, Excel quality, capital-call review, NAV review, valuation review, normalization, portfolio exposure, investor reporting, exception investigation and fund-data Q&A.

Key rule: **the library is capability-driven; financial controls remain deterministic and evidence-backed.**

## Phase 8 — Evidence, Audit & Human-in-the-Loop — COMPLETE
Implemented governed audit capture, immutable run snapshots, evidence extraction, approval lifecycle, actor/decision/reason fields and `/governance` APIs.

Key rule: **material financial outcomes remain deterministic, evidence-backed and reviewable; human approval is explicit and never inferred from an LLM response.**

## Phase 9 — Agent Studio UI — IN PROGRESS
Implemented the hackathon workspace slice with agent library, natural-language composer, independent administrator/fund-manager upload and inspection, mapping review, reconciliation configuration, run status and result views. LLM workflow generation is exposed from the UI when configured.

Remaining polish: richer exception table, audit/evidence drill-down, approval controls and report export.

## Phase 10 — LLM Optimization, Evaluation & Guardrails — COMPLETE
Implemented an optional LangChain/OpenAI LLM layer without moving financial truth into the model:
- structured Pydantic `LLMPlan` generation;
- allow-listed tool selection through the shared `ToolRegistry`;
- deterministic Factory validation after every LLM plan;
- prompt-injection/governance-bypass detection;
- bounded input, output, plan steps and tool selections;
- grounded result explanation with bounded context;
- process-local SHA-256 caching for repeated planning/explanation requests;
- operational LLM/cache metrics without exposing prompts or secrets;
- golden routing evaluation cases across the FundOps catalogue;
- unit tests for guardrails, structured planning and malicious/unknown tool rejection;
- optional operation when no LLM credentials are configured; deterministic Factory remains available.

See `docs/PHASE_10_LLM.md` for configuration and production guidance.

## Phase 11 — Deployment & Security
React → FastAPI → Agent Runtime → PostgreSQL → Object Storage. Add SSO/RBAC/tenant isolation/encryption/secrets/rate limits/observability/CI/CD/backups. Replace process-local LLM cache with bounded Redis in production. Avoid premature Kafka/Kubernetes/microservices.

## Phase 12 — Hackathon Demo & Investor Readiness
Demonstrate a realistic reconciliation workflow, evidence-backed exceptions, export, and generation of a second agent through Agent Factory. Track time saved, exceptions detected, accuracy, evidence coverage, agent creation time and LLM cost.

## Recommended hackathon scope
**Minimum compelling product: Phases 0–8 + Phase 9 workflow + Phase 10 governed LLM planning/explanation.**
