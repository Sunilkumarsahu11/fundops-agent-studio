from typing import Any

from .models import ToolDefinition
from .review_tools import excel_quality_tool, exception_investigation_tool, normalization_review_tool
from .tool_layer import (
    approve_tool, build_exception_report_tool, calculate_variance_tool,
    capture_audit_event_tool, capital_call_review_tool, collect_evidence_tool,
    create_run_snapshot_tool, evaluate_materiality_tool, get_record_evidence_tool,
    ingest_source_tool, inspect_source_tool, investor_reporting_tool,
    map_source_to_model_tool, nav_review_tool, normalize_records_tool,
    portfolio_exposure_tool, query_records_tool, reconcile_records_tool, reject_tool,
    request_approval_tool, validate_records_tool, valuation_review_tool,
)


def echo(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"received": inputs}


def _definition(name: str, description: str) -> ToolDefinition:
    return ToolDefinition(name=name, description=description, input_schema={"type": "object"}, output_schema={"type": "object"})


def register_builtins(registry: Any) -> None:
    tools = [
        (_definition("echo", "Reference deterministic tool used for smoke tests."), echo),
        (_definition("inspect_source", "Inspect an Excel or JSON source and return source structure and locations."), inspect_source_tool),
        (_definition("ingest_source", "Ingest a source into the configured canonical fund model with provenance."), ingest_source_tool),
        (_definition("map_source_to_model", "Generate deterministic source-to-canonical-field mapping candidates."), map_source_to_model_tool),
        (_definition("normalize_records", "Normalize canonical record values according to the configured fund model."), normalize_records_tool),
        (_definition("validate_records", "Validate canonical records against the configured fund model."), validate_records_tool),
        (_definition("query_records", "Filter supplied canonical records without external data access."), query_records_tool),
        (_definition("get_record_evidence", "Return provenance evidence for a supplied canonical record."), get_record_evidence_tool),
        (_definition("reconcile_records", "Deterministically reconcile two independent canonical record sets."), reconcile_records_tool),
        (_definition("calculate_variance", "Calculate absolute and percentage variance between two numeric values."), calculate_variance_tool),
        (_definition("evaluate_materiality", "Classify a variance against a deterministic materiality threshold."), evaluate_materiality_tool),
        (_definition("build_exception_report", "Build an evidence-backed exception report from a reconciliation result."), build_exception_report_tool),
        (_definition("capital_call_review", "Review capital calls for required fields, duplicate keys and positive amounts."), capital_call_review_tool),
        (_definition("nav_review", "Review NAV records for missing, negative and threshold-exceeding NAV movements."), nav_review_tool),
        (_definition("valuation_review", "Review valuation records for amount, currency and valuation-date controls."), valuation_review_tool),
        (_definition("portfolio_exposure", "Aggregate investment exposure by a configured portfolio dimension with percentages."), portfolio_exposure_tool),
        (_definition("investor_reporting", "Build deterministic investor-level reporting totals with uncalled commitment and evidence."), investor_reporting_tool),
        (_definition("excel_quality", "Inspect an Excel workbook for structural, header, row and blank-column quality risks."), excel_quality_tool),
        (_definition("normalization_review", "Normalize mapped canonical records and report deterministic normalization warnings."), normalization_review_tool),
        (_definition("exception_investigation", "Prioritize deterministic exceptions by severity without changing their outcomes."), exception_investigation_tool),
        (_definition("collect_evidence", "Collect provenance evidence from supplied canonical records."), collect_evidence_tool),
        (_definition("create_run_snapshot", "Create a governance snapshot for an agent run."), create_run_snapshot_tool),
        (_definition("capture_audit_event", "Record a governed audit event for an agent run."), capture_audit_event_tool),
        (_definition("request_approval", "Request human approval for a consequential action."), request_approval_tool),
        (_definition("approve", "Approve a pending governed action."), approve_tool),
        (_definition("reject", "Reject a pending governed action."), reject_tool),
    ]
    for definition, handler in tools:
        registry.register(definition, handler)
