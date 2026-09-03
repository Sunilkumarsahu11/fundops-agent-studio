# Phase 7 — Fund Operations Agent Library

## Objective
Provide a reusable catalog of FundOps agents that can be selected directly by Agent Factory workflows or invoked through the API. Agents use canonical fund records and preserve the platform boundary between deterministic controls and future LLM reasoning.

## Catalog

| Agent | Purpose |
|---|---|
| Fund Reconciliation | Compare administrator/manager datasets with tolerances, reason codes, materiality and evidence |
| Excel Quality | Identify workbook structure/header/type risks before ingestion |
| Capital Call Review | Review capital-call completeness and consistency |
| NAV Review | Review NAV data quality and variance risks |
| Valuation Review | Review valuation date/currency/variance consistency |
| Fund Data Normalization | Normalize mapped source data with provenance |
| Portfolio Exposure | Prepare investment exposure views |
| Investor Reporting | Prepare governed reporting datasets |
| Exception Investigation | Prioritize and explain existing deterministic exceptions |
| Fund Data Q&A | Answer questions from supplied canonical records with evidence |

## API

- `GET /fund-ops/agents`
- `GET /fund-ops/agents/{agent_id}`
- `POST /fund-ops/agents/{agent_id}/run`

## Governance

Only explicitly enabled domain handlers execute. Catalogued agents without an implemented handler return `not_implemented`; they never silently execute an unsafe fallback.

Financial reconciliation delegates to the Phase 4 deterministic engine through the Phase 5 `FundReconciliationAgent`. LLMs do not calculate amounts, alter tolerances, determine materiality or override results.

## Phase 7 completion boundary
The library establishes the reusable agent contracts and catalog, fully enables reconciliation, exception investigation and record-based Q&A, and provides governed placeholders for the remaining domain agents. Their specialized workflows can be incrementally enabled in later phases without changing the factory/runtime contract.
