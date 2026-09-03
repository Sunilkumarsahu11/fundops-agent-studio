from __future__ import annotations

from typing import Any

from app.fund_model.records import CanonicalRecord
from .engine import reconcile
from .models import ReconciliationRequest, ReconciliationResult
from .report import build_exception_report


class FundReconciliationAgent:
    """Thin orchestration layer around deterministic controls.

    This class deliberately does not perform financial calculations itself.
    It prepares the reconciliation request, invokes the deterministic engine,
    and returns an evidence-backed report suitable for a future LLM explainer.
    """

    def run(
        self,
        left_records: list[CanonicalRecord],
        right_records: list[CanonicalRecord],
        *,
        key_fields: list[str],
        amount_field: str | None = None,
        date_field: str | None = None,
        currency_field: str | None = None,
        amount_tolerance: float = 0.0,
        amount_tolerance_percent: float = 0.0,
        date_tolerance_days: int = 0,
        materiality_threshold: float = 0.0,
    ) -> tuple[ReconciliationResult, dict[str, Any]]:
        result = reconcile(ReconciliationRequest(
            left_records=left_records,
            right_records=right_records,
            key_fields=key_fields,
            amount_field=amount_field,
            date_field=date_field,
            currency_field=currency_field,
            amount_tolerance=amount_tolerance,
            amount_tolerance_percent=amount_tolerance_percent,
            date_tolerance_days=date_tolerance_days,
            materiality_threshold=materiality_threshold,
        ))
        return result, build_exception_report(result)
