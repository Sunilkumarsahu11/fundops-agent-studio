# Agent Tool Layer

The Agent Runtime now exposes an allow-listed deterministic tool layer. AI planners select these tools; the tools themselves do not delegate financial calculations to an LLM.

## Registered tools

### Source and ingestion
- `inspect_source` — inspect Excel/JSON structure and source locations.
- `ingest_source` — ingest a source into the configured canonical model with provenance.
- `map_source_to_model` — deterministic source-to-canonical mapping candidates.
- `normalize_records` — canonical type normalization.
- `validate_records` — required/nullability/unknown-field validation.

### Fund data
- `query_records` — filter records supplied in the agent context.
- `get_record_evidence` — retrieve provenance for a supplied record.

### Financial controls
- `reconcile_records` — deterministic two-sided reconciliation.
- `calculate_variance` — deterministic amount and percentage variance.
- `evaluate_materiality` — deterministic materiality classification.
- `build_exception_report` — evidence-backed exception report.
- `collect_evidence` — collect provenance evidence from records.

### Governance
- `create_run_snapshot` — create a governance run snapshot.
- `capture_audit_event` — record an audit event.
- `request_approval` — create a human approval request.
- `approve` — approve a pending request.
- `reject` — reject a pending request.

## Safety model

1. Only registered tools can be executed by `ToolRegistry`.
2. Financial calculations remain deterministic Python operations.
3. `reconcile_records` accepts independent `left_records` and `right_records`; it does not duplicate one source into both sides.
4. Source tools require explicit input data; the runtime does not grant arbitrary filesystem or network access.
5. Governance actions are explicit tools and can be placed behind required workflow steps.
6. The existing `echo` tool remains available for runtime smoke tests.

## AI planner contract

The future LLM planner should output only declarative workflow steps using these registered tool names. The runtime validates each required step against the registry before execution. This keeps model reasoning separate from deterministic fund controls.
