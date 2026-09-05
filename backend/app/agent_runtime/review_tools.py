from __future__ import annotations

import base64
from collections import Counter
from typing import Any

from app.fund_model.records import CanonicalRecord
from app.ingestion.models import SourceFormat
from app.ingestion.pipeline import inspect_source

from .tool_layer import normalize_records_tool


def _records(inputs: dict[str, Any]) -> list[CanonicalRecord]:
    return [CanonicalRecord.model_validate(r) for r in inputs.get("records", [])]


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
    if raw_format:
        fmt = SourceFormat(raw_format)
    elif file_name.lower().endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        fmt = SourceFormat.EXCEL
    else:
        fmt = SourceFormat.JSON
    return file_name, content, fmt


def excel_quality_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    file_name, content, fmt = _content(inputs)
    if fmt != SourceFormat.EXCEL:
        raise ValueError("excel_quality requires an Excel source")
    tables = inspect_source(file_name, content, fmt)
    min_columns = int(inputs.get("min_columns", 1))
    min_rows = int(inputs.get("min_rows", 1))
    issues: list[dict[str, Any]] = []
    sheets: list[dict[str, Any]] = []
    for table in tables:
        headers = [column.name for column in table.columns]
        duplicate_headers = [header for header, count in Counter(headers).items() if count > 1]
        row_count = len(table.rows)
        if not headers:
            issues.append(
                {
                    "code": "MISSING_HEADERS",
                    "sheet": table.name,
                    "message": "No usable header row detected",
                }
            )
        if len(headers) < min_columns:
            issues.append(
                {
                    "code": "TOO_FEW_COLUMNS",
                    "sheet": table.name,
                    "message": f"Expected at least {min_columns} columns",
                }
            )
        if row_count < min_rows:
            issues.append(
                {
                    "code": "TOO_FEW_ROWS",
                    "sheet": table.name,
                    "message": f"Expected at least {min_rows} data rows",
                }
            )
        if duplicate_headers:
            issues.append(
                {
                    "code": "DUPLICATE_HEADERS",
                    "sheet": table.name,
                    "headers": duplicate_headers,
                }
            )
        blank_columns = [
            header
            for header in headers
            if not any(row.get(header) not in (None, "") for row in table.rows)
        ]
        if blank_columns:
            issues.append(
                {
                    "code": "BLANK_COLUMNS",
                    "sheet": table.name,
                    "headers": blank_columns,
                }
            )
        sheets.append(
            {
                "sheet": table.name,
                "columns": len(headers),
                "rows": row_count,
                "headers": headers,
                "duplicate_headers": duplicate_headers,
            }
        )
    return {
        "status": "issues" if issues else "passed",
        "file_name": file_name,
        "sheet_count": len(sheets),
        "sheets": sheets,
        "issue_count": len(issues),
        "issues": issues,
    }


def normalization_review_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    result = normalize_records_tool(inputs)
    records = _records({"records": result.get("records", [])})
    warnings = result.get("warnings", [])
    return {
        "status": "warnings" if warnings else "normalized",
        "record_count": len(records),
        "records": [record.model_dump(mode="json") for record in records],
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def exception_investigation_tool(inputs: dict[str, Any]) -> dict[str, Any]:
    exceptions = inputs.get("exceptions", [])
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    default_severity = str(inputs.get("default_severity", "medium")).lower()
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(exceptions):
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", item.get("reason_code", "UNKNOWN_EXCEPTION")))
        severity = str(item.get("severity", default_severity)).lower()
        if severity not in severity_order:
            severity = default_severity if default_severity in severity_order else "medium"
        enriched.append(
            {
                **item,
                "exception_id": str(
                    item.get("exception_id", item.get("record_id", index + 1))
                ),
                "code": code,
                "severity": severity,
                "priority": severity_order[severity],
            }
        )
    enriched.sort(
        key=lambda item: (
            item["priority"],
            str(item["code"]),
            str(item["exception_id"]),
        )
    )
    counts = Counter(item["severity"] for item in enriched)
    return {
        "status": "exceptions" if enriched else "passed",
        "exception_count": len(enriched),
        "severity_counts": dict(counts),
        "exceptions": enriched,
        "principle": (
            "Prioritisation is deterministic; original exception outcomes are unchanged."
        ),
    }
