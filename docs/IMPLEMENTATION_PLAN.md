# FundOps Agent Studio — Implementation Plan

## Product objective

Build a configurable agent platform for private-market fund operations. A fund manager should be able to describe a repetitive workflow in natural language and receive a governed, auditable agent assembled from reusable tools.

## Architecture principles

- LLMs handle intent understanding, semantic mapping, planning, exception explanation and natural-language interaction.
- Deterministic Python services handle arithmetic, reconciliation, tolerances, financial calculations and validation rules.
- Every material result must have evidence/lineage back to the source workbook cell, JSON path or normalized record.
- Agents are declarative workflows rather than bespoke applications.
- Human approval is required before consequential external actions.
- Synthetic/anonymised data only for the hackathon repository.

---

## Phase 0 — Foundation & architecture

**Goal:** establish a clean repository and technical boundaries.

Deliverables:
- Repository structure
- Architecture documentation
- FastAPI backend skeleton
- React frontend skeleton
- Environment configuration
- Docker Compose for local development
- Testing conventions
- Initial domain/tool/workflow package boundaries

Exit criteria:
- Backend starts locally.
- Health endpoint works.
- Frontend starts locally.
- Architecture and implementation plan are documented.

---

## Phase 1 — Agent Runtime

**Goal:** build one reusable execution engine instead of independent agents.

Core components:
- Agent definition
- Task/request model
- Workflow step model
- Tool registry
- Planner
- Executor
- State/context store
- Validation stage
- Retry/error handling
- Execution events

Lifecycle:

```text
RECEIVE → UNDERSTAND → PLAN → EXECUTE → VALIDATE → EXPLAIN → COMPLETE
```

Exit criteria:
- A static workflow can be registered and executed.
- Tool calls and outputs are recorded.
- Failed validation prevents completion.

---

## Phase 2 — Canonical Fund Data Model

**Goal:** provide a common semantic model across Excel, JSON and future sources.

Initial entities:

```text
Fund
Investor
Commitment
CapitalCall
Distribution
PortfolioCompany
Investment
Valuation
Transaction
NAV
FundPeriod
Currency
```

Deliverables:
- Pydantic domain models
- PostgreSQL schema/migrations
- IDs and relationships
- Source/provenance metadata
- Data normalization conventions

Exit criteria:
- Sample fund data can be represented without source-specific field names.

---

## Phase 3 — Data Ingestion & Schema Mapping

**Goal:** turn messy operational files into normalized records.

Tools:
- Excel reader
- JSON reader
- Sheet/table detector
- Header detector
- Type inference
- Currency/date normalization
- Schema mapper
- Entity matching
- Source lineage tracker

Important rule:

> Never silently discard an unmapped field. Record it as an unmapped field or mapping candidate.

Exit criteria:
- Excel and JSON can be ingested into the canonical model.
- Mappings are reviewable.
- Source locations are retained.

---

## Phase 4 — Deterministic Reconciliation Engine

**Goal:** compare datasets reliably without relying on an LLM for numerical correctness.

Capabilities:
- Exact matching
- Fuzzy/entity matching
- Amount comparison
- Date comparison
- Currency conversion hooks
- Tolerance rules
- Missing-record detection
- Duplicate detection
- Sign/convention checks
- Aggregation checks
- Reconciliation status

Example:

```text
Excel NAV        £125.4m
JSON NAV         £124.9m
Difference       £0.5m
Tolerance        £0.1m
Status           EXCEPTION
```

Exit criteria:
- Reconciliation results are deterministic and reproducible.
- Each exception has evidence and reason codes.

---

## Phase 5 — First Production Agent: Fund Reconciliation Agent

**Goal:** deliver the hackathon's main end-to-end vertical slice.

User request example:

> "Compare this quarterly portfolio Excel with the valuation JSON and tell me what could affect NAV."

Workflow:

```text
Upload files
   ↓
Detect schemas
   ↓
Map fields/entities
   ↓
Normalize records
   ↓
Reconcile
   ↓
Run financial validation rules
   ↓
Rank material exceptions
   ↓
Generate explanation
   ↓
Produce evidence-backed report
```

Output:
- Overall reconciliation status
- Exception table
- Materiality ranking
- Source evidence
- Suggested investigation
- Downloadable report

Exit criteria:
- A realistic synthetic example can be demonstrated end-to-end in under a few minutes.

---

## Phase 6 — Agent Factory

**Goal:** allow a fund manager to create a new agent from natural language.

Example:

> "Create an agent that checks capital calls against investor commitments and flags anything over the remaining commitment."

Factory pipeline:

```text
Natural-language request
        ↓
Intent classification
        ↓
Task/domain identification
        ↓
Required inputs
        ↓
Workflow generation
        ↓
Tool selection
        ↓
Validation of generated workflow
        ↓
Human review
        ↓
Publish agent
```

Introduce a declarative workflow format such as YAML/JSON so generated workflows can be reviewed, versioned and tested.

Example:

```yaml
id: capital-call-validator
input:
  - investor_commitments
  - capital_calls
steps:
  - tool: normalize_entities
  - tool: calculate_remaining_commitment
  - tool: validate_commitment_limit
  - tool: generate_exceptions
output:
  format: report
```

Exit criteria:
- At least three agent types can be generated from reusable tools.

---

## Phase 7 — Fund Operations Agent Library

Build reusable templates based on real fund-manager requests.

### Priority agents

1. Fund Reconciliation Agent
2. Excel Quality/Risk Scanner
3. Capital Call Validator
4. NAV Reconciliation Agent
5. Valuation Review Agent
6. Fund Data Normalisation Agent
7. Portfolio Exposure Agent
8. Investor Reporting Agent
9. Exception Investigation Agent
10. Fund Data Q&A Agent

Each agent should reuse the same runtime and tool registry.

---

## Phase 8 — Evidence, Audit & Human-in-the-Loop

**Goal:** make the system trustworthy for financial operations.

Capabilities:
- Source cell/JSON-path references
- Evidence bundles
- Execution history
- Workflow versioning
- Agent versioning
- Decision logs
- Confidence indicators
- Approval/rejection workflow
- Before/after snapshots
- Immutable-ish audit records

No consequential action should be hidden behind an autonomous LLM decision.

---

## Phase 9 — Agent Studio UI

Build a polished React interface.

Screens:

```text
Dashboard
  ├── Agents
  ├── Runs
  ├── Exceptions
  ├── Data Sources
  └── Audit

Agent Builder
  ├── Natural-language request
  ├── Generated workflow
  ├── Inputs
  ├── Tools
  ├── Rules
  └── Publish

Run Detail
  ├── Status
  ├── Workflow trace
  ├── Exceptions
  ├── Evidence
  └── Export
```

Hackathon UX priority:
- Upload files
- Describe task
- Watch agent execute
- Review exceptions
- Inspect evidence
- Export result

---

## Phase 10 — LLM Optimization, Evaluation & Guardrails

**Goal:** make agent behaviour reliable and cost-controlled.

Capabilities:
- Prompt/version management
- Structured outputs
- Model routing
- Token/cost tracking
- Cached semantic mappings
- Deterministic tool execution
- Evaluation datasets
- Golden test cases
- Hallucination checks
- Numeric consistency checks
- Prompt-injection defenses for uploaded documents

Important:

> LLM output must never be treated as the source of truth for financial arithmetic.

---

## Phase 11 — Deployment & Security

Hackathon deployment should remain simple.

Target architecture:

```text
React
  ↓
FastAPI
  ↓
Agent Runtime
  ↓
PostgreSQL
  ↓
Object Storage
```

Later production capabilities:
- Authentication/SSO
- RBAC
- Tenant isolation
- Encryption
- Secrets management
- Rate limiting
- Observability
- CI/CD
- Container deployment
- Backup/recovery

Avoid premature microservices/Kafka/Kubernetes for the hackathon MVP.

---

## Phase 12 — Hackathon Demo & Investor Readiness

**Goal:** demonstrate a compelling fund-manager workflow rather than a generic AI chatbot.

Demo narrative:

1. Fund manager uploads an Excel workbook and valuation JSON.
2. Manager asks: "Reconcile these and tell me what could affect NAV."
3. Agent identifies schemas and entities.
4. Agent executes deterministic reconciliation.
5. Material discrepancies are ranked.
6. Each discrepancy is linked to source evidence.
7. Agent explains likely causes.
8. Manager approves/export results.
9. Manager asks for a similar workflow.
10. Agent Factory generates a reusable new agent.

### Success metrics

- Time saved versus manual spreadsheet review
- Number of exceptions detected
- False-positive rate
- Reconciliation accuracy
- Percentage of results with source evidence
- Agent creation time
- LLM cost per run

### Final pitch

> **FundOps Agent Studio turns repetitive private-market spreadsheet workflows into governed, auditable AI agents — without requiring fund managers to build software.**

---

## Recommended build order

For the hackathon, do not attempt every phase fully.

```text
Phase 0  ██████████
Phase 1  ██████████
Phase 2  ████████
Phase 3  ██████████
Phase 4  ██████████
Phase 5  ██████████  ← demo-critical
Phase 6  ██████████  ← differentiation
Phase 7  ████
Phase 8  ██████
Phase 9  ████████
Phase 10 ████
Phase 11 ██
Phase 12 ██████████
```

The minimum compelling product is **Phases 0–6 + a thin slice of 8–9**.
