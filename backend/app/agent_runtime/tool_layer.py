from __future__ import annotations

import base64
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.fund_model.persistence import FundModelStore
from app.fund_model.records import CanonicalRecord
from app.ingestion.mapper import suggest_mappings
from app.ingestion.models import SourceFormat
from app.ingestion.normalizer import normalize_value
from app.ingestion.pipeline import ingest, inspect_source
from app.reconciliation.engine import reconcile
from app.reconciliation.models import ReconciliationRequest
from app.reconciliation.report import build_exception_report
from app.governance.models import ApprovalRequest
from app.api.governance_router import service as governance_service


def _content(inputs: dict[str, Any]) -> tuple[str, bytes, SourceFormat]:
    file_name = str(inputs["file_name"])
    encoded = inputs.get("content_base64")
    if not isinstance(encoded, str):
        raise ValueError("content_base64 is required")
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError("content_base64 is not valid base64") from exc
    raw_format = inputs.get("source_format")
    fmt = SourceFormat(raw_format) if raw_format else SourceFormat.EXCEL if file_name.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")) else SourceFormat.JSON
    return file_name, content, fmt


def _records(inputs: dict[str, Any]) -> list[CanonicalRecord]:
    return [CanonicalRecord.model_validate(r) for r in inputs.get("records", [])]


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inspect_source_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    file_name, content, fmt = _content(inputs)
    return {"file_name": file_name, "format": fmt.value, "tables": [t.model_dump(mode="json") for t in inspect_source(file_name, content, fmt)]}


def ingest_source_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    file_name, content, fmt = _content(inputs)
    model_id = str(inputs["model_id"])
    version = inputs.get("model_version")
    model = FundModelStore(get_settings().database_url).get(model_id, int(version) if version is not None else None)
    if model is None:
        raise ValueError(f"Fund model not found: {model_id}")
    result = ingest(file_name, content, fmt, model, tenant_id=inputs.get("tenant_id"))
    return result.model_dump(mode="json")


def map_source_to_model_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    model_id = str(inputs["model_id"])
    version = inputs.get("model_version")
    model = FundModelStore(get_settings().database_url).get(model_id, int(version) if version is not None else None)
    if model is None:
        raise ValueError(f"Fund model not found: {model_id}")
    tables = inputs.get("tables", [])
    from app.ingestion.models import SourceTable
    parsed = [SourceTable.model_validate(t) for t in tables]
    return suggest_mappings(parsed, model).model_dump(mode="json")


def normalize_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    model_id = str(inputs["model_id"])
    version = inputs.get("model_version")
    model = FundModelStore(get_settings().database_url).get(model_id, int(version) if version is not None else None)
    if model is None:
        raise ValueError(f"Fund model not found: {model_id}")
    records = _records(inputs)
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    for record in records:
        entity = next((e for e in model.entities if e.name == record.entity), None)
        if entity is None:
            warnings.append(f"Unknown entity: {record.entity}")
            normalized.append(record.model_dump(mode="json"))
            continue
        data = dict(record.data)
        for field in entity.fields:
            if field.name in data and data[field.name] is not None:
                try:
                    data[field.name] = normalize_value(data[field.name], field.type.value)
                except ValueError as exc:
                    warnings.append(f"{record.record_id} {field.name}: {exc}")
        record.data = data
        normalized.append(record.model_dump(mode="json"))
    return {"records": normalized, "warnings": warnings}


def validate_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    model_id = str(inputs["model_id"])
    version = inputs.get("model_version")
    model = FundModelStore(get_settings().database_url).get(model_id, int(version) if version is not None else None)
    if model is None:
        raise ValueError(f"Fund model not found: {model_id}")
    errors: list[str] = []
    warnings: list[str] = []
    for raw in inputs.get("records", []):
        record = CanonicalRecord.model_validate(raw)
        entity = next((e for e in model.entities if e.name == record.entity), None)
        if entity is None:
            errors.append(f"{record.record_id}: unknown entity {record.entity}")
            continue
        for field in entity.fields:
            value = record.data.get(field.name)
            if field.required and value is None:
                errors.append(f"{record.record_id}: required field missing: {field.name}")
            if value is None and not field.nullable and not field.required:
                errors.append(f"{record.record_id}: non-nullable field is null: {field.name}")
        for name in record.data:
            if not any(f.name == name for f in entity.fields):
                warnings.append(f"{record.record_id}: field not in model: {name}")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def query_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    entity = inputs.get("entity")
    filters = inputs.get("filters", {})
    matches = []
    for record in records:
        if entity and record.entity != entity:
            continue
        if all(record.data.get(k) == v for k, v in filters.items()):
            matches.append(record.model_dump(mode="json"))
    return {"count": len(matches), "records": matches, "evidence": [r.source_evidence() for r in (CanonicalRecord.model_validate(x) for x in matches)]}


def get_record_evidence_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    target = str(inputs["record_id"])
    for record in _records(inputs):
        if str(record.record_id) == target:
            return {"record_id": target, "evidence": record.source_evidence()}
    return {"record_id": target, "evidence": []}


def reconcile_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    request = ReconciliationRequest(
        left_records=[CanonicalRecord.model_validate(r) for r in inputs.get("left_records", [])],
        right_records=[CanonicalRecord.model_validate(r) for r in inputs.get("right_records", [])],
        key_fields=inputs["key_fields"], amount_field=inputs.get("amount_field"), date_field=inputs.get("date_field"),
        currency_field=inputs.get("currency_field"), amount_tolerance=inputs.get("amount_tolerance", 0.0),
        amount_tolerance_percent=inputs.get("amount_tolerance_percent", 0.0), date_tolerance_days=inputs.get("date_tolerance_days", 0),
        materiality_threshold=inputs.get("materiality_threshold", 0.0), enable_fuzzy_matching=False,
    )
    return reconcile(request).model_dump(mode="json")


def calculate_variance_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    left = float(inputs["left"])
    right = float(inputs["right"])
    variance = left - right
    denominator = max(abs(left), abs(right), 1e-12)
    return {"left": left, "right": right, "variance": variance, "absolute_variance": abs(variance), "variance_percent": abs(variance) / denominator * 100}


def evaluate_materiality_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    variance = abs(float(inputs.get("variance", 0)))
    threshold = float(inputs.get("threshold", 0))
    return {"material": variance > 0 if threshold <= 0 else variance >= threshold, "variance": variance, "threshold": threshold}


def build_exception_report_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.reconciliation.models import ReconciliationResult
    return build_exception_report(ReconciliationResult.model_validate(inputs["reconciliation_result"]))


def collect_evidence_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    return {"evidence": [{"record_id": str(r.record_id), "entity": r.entity, "provenance": r.source_evidence()} for r in records]}


def capital_call_review_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    required = inputs.get("required_fields", ["fund_id", "call_id", "amount"])
    amount_field = str(inputs.get("amount_field", "amount"))
    id_fields = inputs.get("id_fields", ["fund_id", "call_id"])
    exceptions: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        data = record.data
        missing = [f for f in required if data.get(f) in (None, "")]
        amount = _number(data.get(amount_field))
        key = tuple(data.get(f) for f in id_fields)
        if key in seen:
            exceptions.append({"record_id": str(record.record_id), "code": "DUPLICATE_CAPITAL_CALL", "message": f"Duplicate capital call key: {key}", "evidence": record.source_evidence()})
        seen.add(key)
        if missing:
            exceptions.append({"record_id": str(record.record_id), "code": "MISSING_REQUIRED_FIELD", "message": f"Missing required fields: {missing}", "evidence": record.source_evidence()})
        if amount is not None and amount <= 0:
            exceptions.append({"record_id": str(record.record_id), "code": "INVALID_CALL_AMOUNT", "message": "Capital call amount must be positive", "evidence": record.source_evidence()})
    return {"status": "exceptions" if exceptions else "passed", "record_count": len(records), "exception_count": len(exceptions), "exceptions": exceptions, "total_call_amount": sum(_number(r.data.get(amount_field)) or 0 for r in records)}


def nav_review_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    nav_field = str(inputs.get("nav_field", "nav"))
    fund_field = str(inputs.get("fund_field", "fund_id"))
    prior_field = inputs.get("prior_nav_field", "prior_nav")
    threshold = float(inputs.get("variance_percent_threshold", 0.0))
    exceptions: list[dict[str, Any]] = []
    for record in records:
        nav = _number(record.data.get(nav_field))
        if nav is None:
            exceptions.append({"record_id": str(record.record_id), "code": "MISSING_NAV", "message": f"Missing or non-numeric {nav_field}", "evidence": record.source_evidence()})
            continue
        if nav < 0:
            exceptions.append({"record_id": str(record.record_id), "code": "NEGATIVE_NAV", "message": "NAV cannot be negative", "evidence": record.source_evidence()})
        prior = _number(record.data.get(prior_field)) if prior_field else None
        if prior is not None and prior != 0:
            pct = abs(nav - prior) / abs(prior) * 100
            if pct >= threshold > 0:
                exceptions.append({"record_id": str(record.record_id), "code": "NAV_VARIANCE", "message": f"NAV changed by {pct:.2f}%", "variance_percent": pct, "evidence": record.source_evidence()})
    totals: dict[str, float] = defaultdict(float)
    for r in records:
        value = _number(r.data.get(nav_field))
        if value is not None:
            totals[str(r.data.get(fund_field, "unknown"))] += value
    return {"status": "exceptions" if exceptions else "passed", "record_count": len(records), "exception_count": len(exceptions), "exceptions": exceptions, "nav_by_fund": dict(totals)}


def valuation_review_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    amount_field = str(inputs.get("amount_field", "fair_value"))
    currency_field = str(inputs.get("currency_field", "currency"))
    date_field = str(inputs.get("date_field", "valuation_date"))
    allowed_currencies = {str(x).upper() for x in inputs.get("allowed_currencies", [])}
    exceptions: list[dict[str, Any]] = []
    for record in records:
        data = record.data
        amount = _number(data.get(amount_field))
        if amount is None:
            exceptions.append({"record_id": str(record.record_id), "code": "MISSING_VALUATION", "message": f"Missing or non-numeric {amount_field}", "evidence": record.source_evidence()})
        elif amount < 0 and not inputs.get("allow_negative", False):
            exceptions.append({"record_id": str(record.record_id), "code": "NEGATIVE_VALUATION", "message": "Valuation cannot be negative", "evidence": record.source_evidence()})
        currency = data.get(currency_field)
        if not currency:
            exceptions.append({"record_id": str(record.record_id), "code": "MISSING_CURRENCY", "message": "Valuation currency is required", "evidence": record.source_evidence()})
        elif allowed_currencies and str(currency).upper() not in allowed_currencies:
            exceptions.append({"record_id": str(record.record_id), "code": "UNSUPPORTED_CURRENCY", "message": f"Currency {currency} is not allowed", "evidence": record.source_evidence()})
        if not data.get(date_field):
            exceptions.append({"record_id": str(record.record_id), "code": "MISSING_VALUATION_DATE", "message": "Valuation date is required", "evidence": record.source_evidence()})
    return {"status": "exceptions" if exceptions else "passed", "record_count": len(records), "exception_count": len(exceptions), "exceptions": exceptions}


def portfolio_exposure_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    amount_field = str(inputs.get("amount_field", "fair_value"))
    group_field = str(inputs.get("group_field", "sector"))
    currency_field = str(inputs.get("currency_field", "currency"))
    groups: dict[str, float] = defaultdict(float)
    currencies: set[str] = set()
    for record in records:
        amount = _number(record.data.get(amount_field))
        if amount is None:
            continue
        groups[str(record.data.get(group_field, "Unclassified"))] += amount
        if record.data.get(currency_field):
            currencies.add(str(record.data[currency_field]).upper())
    total = sum(groups.values())
    exposure = [{"group": group, "amount": amount, "percentage": amount / total * 100 if total else 0.0} for group, amount in sorted(groups.items(), key=lambda x: abs(x[1]), reverse=True)]
    return {"record_count": len(records), "total_exposure": total, "currencies": sorted(currencies), "group_field": group_field, "exposure": exposure}


def investor_reporting_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs)
    investor_field = str(inputs.get("investor_field", "investor_id"))
    metric_fields = inputs.get("metric_fields", ["commitment", "capital_called", "distribution", "nav"])
    report: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        investor = str(record.data.get(investor_field, "Unassigned"))
        for field in metric_fields:
            value = _number(record.data.get(field))
            if value is not None:
                report[investor][field] += value
        evidence[investor].append({"record_id": str(record.record_id), "provenance": record.source_evidence()})
    rows = []
    for investor, metrics in sorted(report.items()):
        row = {"investor": investor, **dict(metrics), "evidence_count": len(evidence[investor])}
        commitment = metrics.get("commitment", 0.0)
        called = metrics.get("capital_called", 0.0)
        row["uncalled_commitment"] = commitment - called
        rows.append(row)
    return {"investor_count": len(rows), "record_count": len(records), "rows": rows, "evidence": dict(evidence)}


def build_exception_report_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.reconciliation.models import ReconciliationResult
    return build_exception_report(ReconciliationResult.model_validate(inputs["reconciliation_result"]))


def create_run_snapshot_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    run_id = UUID(str(inputs["run_id"]))
    from app.governance.models import RunSnapshot
    snapshot = RunSnapshot(run_id=run_id, agent_id=str(inputs["agent_id"]), agent_version=str(inputs.get("agent_version", "1.0.0")), request=inputs.get("request", {}), output=inputs.get("output", {}), status=str(inputs.get("status", "completed")))
    governance_service.snapshots[run_id] = snapshot
    return snapshot.model_dump(mode="json")


def capture_audit_event_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.governance.models import AuditAction, AuditEvent
    event = AuditEvent(run_id=UUID(str(inputs["run_id"])), agent_id=inputs.get("agent_id"), action=AuditAction(inputs.get("action", "step_executed")), actor=inputs.get("actor", "system"), message=str(inputs["message"]), details=inputs.get("details", {}))
    return governance_service.record_event(event).model_dump(mode="json")


def request_approval_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    request = ApprovalRequest(run_id=UUID(str(inputs["run_id"])), action=str(inputs["action"]), requested_by=str(inputs["requested_by"]), reason=str(inputs.get("reason", "")))
    return governance_service.request_approval(request).model_dump(mode="json")


def approve_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    result = governance_service.decide(UUID(str(inputs["approval_id"])), approved=True, decided_by=str(inputs["decided_by"]), comment=str(inputs.get("comment", "")))
    return result.model_dump(mode="json")


def reject_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    result = governance_service.decide(UUID(str(inputs["approval_id"])), approved=False, decided_by=str(inputs["decided_by"]), comment=str(inputs.get("comment", "")))
    return result.model_dump(mode="json")
