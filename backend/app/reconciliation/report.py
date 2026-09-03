from __future__ import annotations

from typing import Any

from .models import ReconciliationResult


def build_exception_report(result: ReconciliationResult) -> dict[str, Any]:
    """Create an API/UI-friendly report while preserving deterministic results."""
    exceptions = [
        item.model_dump(mode="json")
        for item in result.matches
        if item.status.value not in {"matched", "matched_within_tolerance"}
        or item.reason_codes
    ]
    return {
        "reconciliation_id": str(result.reconciliation_id),
        "status": result.status,
        "summary": result.summary.model_dump(mode="json"),
        "exceptions": exceptions,
        "exception_count": len(exceptions),
    }
