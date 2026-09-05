import base64
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
from .ylookup_tools import bank_statement_review_tool, bank_workbook_control_tool, investor_loader_control_tool, journal_entry_control_tool, mapping_gap_control_tool, movements_control_tool, workbook_sheet_summary
from .ylookup_transform_tools import bank_pdf_to_canonical_tool, bank_transactions_to_journal_entries_tool, investor_gl_to_loader_tool, loader_reconciliation_tool, loader_rows_from_workbook_tool

def echo(inputs: dict[str, Any]) -> dict[str, Any]: return {"received": inputs}
def ylookup_workbook_summary_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    raw=base64.b64decode(inputs["content_base64"],validate=True); return {"file_name":inputs.get("file_name"),"sheets":workbook_sheet_summary(raw)}
def _definition(name: str, description: str) -> ToolDefinition: return ToolDefinition(name=name,description=description,input_schema={"type":"object"},output_schema={"type":"object"})
def register_builtins(registry: Any) -> None:
    tools=[
      (_definition("echo","Reference deterministic tool used for smoke tests."),echo),
      (_definition("inspect_source","Inspect an Excel or JSON source."),inspect_source_tool),(_definition("ingest_source","Ingest a source into the canonical fund model."),ingest_source_tool),(_definition("map_source_to_model","Generate source-to-model mappings."),map_source_to_model_tool),(_definition("normalize_records","Normalize canonical records."),normalize_records_tool),(_definition("validate_records","Validate canonical records."),validate_records_tool),(_definition("query_records","Filter canonical records."),query_records_tool),(_definition("get_record_evidence","Return record provenance."),get_record_evidence_tool),(_definition("reconcile_records","Reconcile two record sets."),reconcile_records_tool),(_definition("calculate_variance","Calculate numeric variance."),calculate_variance_tool),(_definition("evaluate_materiality","Evaluate variance materiality."),evaluate_materiality_tool),(_definition("build_exception_report","Build reconciliation exception report."),build_exception_report_tool),(_definition("capital_call_review","Review capital calls."),capital_call_review_tool),(_definition("nav_review","Review NAV records."),nav_review_tool),(_definition("valuation_review","Review valuations."),valuation_review_tool),(_definition("portfolio_exposure","Aggregate portfolio exposure."),portfolio_exposure_tool),(_definition("investor_reporting","Build investor reporting."),investor_reporting_tool),(_definition("excel_quality","Inspect Excel quality."),excel_quality_tool),(_definition("normalization_review","Review normalization."),normalization_review_tool),(_definition("exception_investigation","Prioritize exceptions."),exception_investigation_tool),(_definition("collect_evidence","Collect provenance evidence."),collect_evidence_tool),(_definition("create_run_snapshot","Create run governance snapshot."),create_run_snapshot_tool),(_definition("capture_audit_event","Record audit event."),capture_audit_event_tool),(_definition("request_approval","Request human approval."),request_approval_tool),(_definition("approve","Approve governed action."),approve_tool),(_definition("reject","Reject governed action."),reject_tool),
      (_definition("ylookup_workbook_summary","Summarize Ylookup workbook sheets."),ylookup_workbook_summary_tool),(_definition("ylookup_bank_statement_review","Review Ylookup bank statement PDF."),bank_statement_review_tool),(_definition("ylookup_bank_workbook_control","Validate bank working workbook mappings."),bank_workbook_control_tool),(_definition("ylookup_journal_entry_control","Validate Ylookup journal entries."),journal_entry_control_tool),(_definition("ylookup_investor_loader_control","Validate investor GL mappings and balancing."),investor_loader_control_tool),(_definition("ylookup_mapping_gap_control","Extract unresolved loader mapping gaps."),mapping_gap_control_tool),(_definition("ylookup_movements_control","Validate loader movement reconciliation."),movements_control_tool),
      (_definition("ylookup_bank_pdf_to_canonical","Convert bank statement PDF to canonical transactions."),bank_pdf_to_canonical_tool),(_definition("ylookup_bank_to_journal","Transform canonical bank transactions into journal lines using workbook mappings."),bank_transactions_to_journal_entries_tool),(_definition("ylookup_investor_gl_to_loader","Transform investor-level GL into Phase I loader rows using verified mappings."),investor_gl_to_loader_tool),(_definition("ylookup_loader_rows","Read verified loader rows into JSON records."),loader_rows_from_workbook_tool),(_definition("ylookup_loader_reconciliation","Reconcile generated loader rows against verified loader rows."),loader_reconciliation_tool),
    ]
    for definition,handler in tools: registry.register(definition,handler)
