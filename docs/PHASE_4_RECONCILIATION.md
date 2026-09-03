# Phase 4 — Deterministic Reconciliation Engine

## Goal

Compare two sets of canonical fund records and produce an explainable exception report without allowing an LLM to make financial calculations or materiality decisions.

## Flow

`CanonicalRecord A + CanonicalRecord B → key matching → duplicate/missing detection → amount/date/currency/sign rules → tolerance → materiality → reason codes → provenance evidence → summary`

## Supported controls

- Exact composite-key matching.
- Duplicate detection on either side.
- Missing-left and missing-right detection.
- Absolute and percentage amount tolerances.
- Amount variance and sign checks.
- Currency mismatch detection.
- Date variance with configurable day tolerance.
- Materiality classification based on deterministic threshold.
- Reason codes for downstream agent explanations.
- Source evidence from every canonical record's provenance.
- Aggregate summary of counts and total absolute variance.

## API

`POST /reconciliation/run`

The API accepts two canonical-record datasets and configuration for keys, amount/date/currency fields, tolerances, and materiality.

## Design rule

The reconciliation engine is deterministic. LLMs can later explain exceptions, propose mappings, or draft operational summaries, but cannot alter arithmetic, tolerances, matching outcomes, or materiality classification.

## Example

```json
{
  "key_fields": ["valuation_id"],
  "amount_field": "value",
  "currency_field": "currency",
  "date_field": "valuation_date",
  "amount_tolerance": 1000,
  "amount_tolerance_percent": 0.1,
  "date_tolerance_days": 1,
  "materiality_threshold": 5000
}
```

## Next

Phase 5 wraps this engine in the **Fund Reconciliation Agent**, connecting ingestion, model validation, reconciliation, exception ranking, and evidence-backed explanations into one workflow.
