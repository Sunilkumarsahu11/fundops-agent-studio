from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from app.fund_model.persistence import FundModelStore
from app.ingestion.models import SourceFormat
from app.ingestion.pipeline import ingest, inspect_source
from app.fund_model.records import CanonicalRecord
from app.reconciliation.engine import reconcile
from app.reconciliation.models import ReconciliationRequest
from app.reconciliation.report import build_exception_report


def _records(value: Any) -> list[CanonicalRecord]:
    if not isinstance(value, list):
        raise ValueError("records must be a list")
    return [item if isinstance(item, CanonicalRecord) else CanonicalRecord.model_validate(item) for item in value]


def inspect_source_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    file_name = str(inputs["file_name"])
    content = inputs["content"]
    if isinstance(content, str):
        content = content.encode("utf-8")
    source_format = SourceFormat(inputs.get("format") or ("excel" if file_name.lower().endswith((".xlsx", ".xlsm")) else "json"))
    return {"file_name": file_name, "format": source_format.value, "tables": [t.model_dump(mode="json") for t in inspect_source(file_name, content, source_format)]}


def ingest_source_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.core.config import get_settings
    store = FundModelStore(get_settings().database_url)
    model = store.get(str(inputs["model_id"]), inputs.get("model_version"))
    if model is None:
        raise ValueError("Fund model not found")
    file_name = str(inputs["file_name"])
    content = inputs["content"]
    if isinstance(content, str):
        content = content.encode("utf-8")
    fmt = SourceFormat(inputs.get("format") or ("excel" if file_name.lower().endswith((".xlsx", ".xlsm")) else "json"))
    result = ingest(file_name, content, fmt, model, tenant_id=inputs.get("tenant_id"), ingestion_run_id=UUID(str(inputs["ingestion_run_id"])) if inputs.get("ingestion_run_id") else None)
    return result.model_dump(mode="json")


def map_source_to_model_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.ingestion.mapper import suggest_mappings
    from app.fund_model.schema import FundModelDefinition
    model = FundModelDefinition.model_validate(inputs["model"])
    return suggest_mappings(inputs["tables"], model).model_dump(mode="json")


def normalize_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.ingestion.normalizer import normalize_value
    from app.fund_model.schema import FieldType
    field_types = inputs.get("field_types", {})
    output = []
    for record in _records(inputs["records"]):
        data = {k: normalize_value(v, field_types[k]) if k in field_types and v is not None else v for k, v in record.data.items()}
        output.append(record.model_copy(update={"data": data}).model_dump(mode="json"))
    return {"records": output}


def validate_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.fund_model.schema import FundModelDefinition
    model = FundModelDefinition.model_validate(inputs["model"])
    errors = []
    for record in _records(inputs["records"]):
        entity = next((e for e in model.entities if e.name == record.entity), None)
        if entity is None:
            errors.append(f"Unknown entity: {record.entity}")
            continue
        for field in entity.fields:
            if field.required and field.name not in record.data:
                errors.append(f"{record.entity}.{field.name} is required")
    return {"valid": not errors, "errors": errors, "record_count": len(inputs["records"])}


def query_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs["records"])
    filters = inputs.get("filters", {})
    matches = [r.model_dump(mode="json") for r in records if all(str(r.data.get(k, "")).casefold() == str(v).casefold() for k, v in filters.items())]
    return {"records": matches, "count": len(matches)}


def get_record_evidence_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    records = _records(inputs["records"])
    wanted = str(inputs.get("record_id", ""))
    matches = [r for r in records if str(r.record_id) == wanted]
    return {"record_id": wanted, "evidence": [r.source_evidence() for r in matches]}


def reconcile_records_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    request = ReconciliationRequest(
        left_records=_records(inputs["left_records"]), right_records=_records(inputs["right_records"]),
        key_fields=inputs["key_fields"], amount_field=inputs.get("amount_field"), date_field=inputs.get("date_field"),
        currency_field=inputs.get("currency_field"), amount_tolerance=inputs.get("amount_tolerance", 0.0),
        amount_tolerance_percent=inputs.get("amount_tolerance_percent", 0.0), date_tolerance_days=inputs.get("date_tolerance_days", 0),
        materiality_threshold=inputs.get("materiality_threshold", 0.0),
    )
    return reconcile(request).model_dump(mode="json")


def calculate_variance_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    left = float(inputs["left"])
    right = float(inputs["right"])
    variance = left - right
    pct = abs(variance) / max(abs(left), abs(right), 1e-12) * 100
    return {"left": left, "right": right, "variance": variance, "absolute_variance": abs(variance), "variance_percent": pct}


def evaluate_materiality_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    variance = abs(float(inputs["variance"]))
    threshold = float(inputs.get("threshold", 0))
    return {"materiality": "material" if variance > 0 if threshold <= 0 else variance >= threshold else "immaterial", "variance": variance, "threshold": threshold}


def build_exception_report_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    from app.reconciliation.models import ReconciliationResult
    return build_exception_report(ReconciliationResult.model_validate(inputs["reconciliation"]))


def collect_evidence_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"evidence": [r.source_evidence() for r in _records(inputs["records"])]}
