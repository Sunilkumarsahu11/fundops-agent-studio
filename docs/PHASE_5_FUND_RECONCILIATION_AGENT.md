# Phase 5 — Fund Reconciliation Agent

## Objective

Turn the Phase 3 ingestion pipeline and Phase 4 deterministic reconciliation engine into one reusable fund-operations workflow.

## Workflow

`Source datasets → canonical records → deterministic reconciliation → materiality → evidence-backed exception report`

The agent is an orchestration boundary. It does not duplicate financial logic from the reconciliation engine.

## Endpoints

### `POST /fund-reconciliation/run`

Runs the Fund Reconciliation Agent and returns the complete deterministic reconciliation result.

### `POST /fund-reconciliation/report`

Runs the same controls and returns a UI/export-friendly exception report containing:

- reconciliation status;
- summary counts;
- total absolute variance;
- exception count;
- reason codes;
- variance amounts;
- materiality;
- source evidence from both sides.

## Governance boundary

The agent never lets an LLM calculate amounts, alter tolerances, determine materiality, or override a reconciliation outcome. A future LLM layer may explain already-computed exceptions in natural language, with the evidence bundle passed into the prompt.

## Current scope

This phase accepts canonical records directly. The next integration step can connect multipart ingestion/upload sessions to this agent so a user can upload two files and run the workflow without constructing canonical records manually.

## Demo scenario

Compare an administrator valuation workbook against a manager valuation workbook using `valuation_id`, `value`, `currency`, and `valuation_date`. The result identifies missing valuations, duplicates and financial variances and provides the exact source provenance needed for an operations user to investigate.
