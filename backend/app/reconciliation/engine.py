from __future__ import annotations

from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

from .models import (
    ReasonCode,
    RecordMatch,
    ReconciliationRequest,
    ReconciliationResult,
    ReconciliationStatus,
    ReconciliationSummary,
)


def _key(record: Any, fields: list[str]) -> tuple[str, ...]:
    return tuple(str(record.data.get(field, "")).strip().casefold() for field in fields)


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("£", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _materiality(abs_variance: float, threshold: float) -> str:
    if threshold <= 0:
        return "material" if abs_variance > 0 else "immaterial"
    return "material" if abs_variance >= threshold else "immaterial"


def _evidence(left: Any | None, right: Any | None) -> dict[str, Any]:
    return {
        "left": left.source_evidence() if left else [],
        "right": right.source_evidence() if right else [],
    }


def reconcile(request: ReconciliationRequest) -> ReconciliationResult:
    left_by_key: dict[tuple[str, ...], list[Any]] = {}
    right_by_key: dict[tuple[str, ...], list[Any]] = {}
    for record in request.left_records:
        left_by_key.setdefault(_key(record, request.key_fields), []).append(record)
    for record in request.right_records:
        right_by_key.setdefault(_key(record, request.key_fields), []).append(record)

    results: list[RecordMatch] = []
    matched_right: set[str] = set()
    all_keys = set(left_by_key) | set(right_by_key)

    for key in sorted(all_keys):
        lefts = left_by_key.get(key, [])
        rights = right_by_key.get(key, [])
        if len(lefts) > 1 or len(rights) > 1:
            for record in lefts:
                results.append(RecordMatch(
                    left_record_id=record.record_id, status=ReconciliationStatus.DUPLICATE,
                    reason_codes=[ReasonCode.DUPLICATE_LEFT], evidence=_evidence(record, None),
                ))
            for record in rights:
                results.append(RecordMatch(
                    right_record_id=record.record_id, status=ReconciliationStatus.DUPLICATE,
                    reason_codes=[ReasonCode.DUPLICATE_RIGHT], evidence=_evidence(None, record),
                ))
            matched_right.update(str(r.record_id) for r in rights)
            continue
        if not lefts:
            r = rights[0]
            results.append(RecordMatch(right_record_id=r.record_id, status=ReconciliationStatus.MISSING_LEFT,
                reason_codes=[ReasonCode.MISSING_LEFT], evidence=_evidence(None, r)))
            continue
        if not rights:
            l = lefts[0]
            results.append(RecordMatch(left_record_id=l.record_id, status=ReconciliationStatus.MISSING_RIGHT,
                reason_codes=[ReasonCode.MISSING_RIGHT], evidence=_evidence(l, None)))
            continue

        l, r = lefts[0], rights[0]
        matched_right.add(str(r.record_id))
        reasons: list[ReasonCode] = [ReasonCode.EXACT_MATCH]
        status = ReconciliationStatus.MATCHED
        amount_left = _number(l.data.get(request.amount_field)) if request.amount_field else None
        amount_right = _number(r.data.get(request.amount_field)) if request.amount_field else None
        variance = None if amount_left is None or amount_right is None else amount_left - amount_right
        abs_variance = abs(variance) if variance is not None else 0.0
        variance_pct = None
        if amount_left is not None and amount_right is not None:
            denominator = max(abs(amount_left), abs(amount_right), 1e-12)
            variance_pct = abs_variance / denominator * 100
            if (amount_left < 0) != (amount_right < 0) and amount_left != 0 and amount_right != 0:
                reasons.append(ReasonCode.SIGN_MISMATCH)
            within = abs_variance <= request.amount_tolerance or variance_pct <= request.amount_tolerance_percent
            if not within:
                reasons.append(ReasonCode.AMOUNT_VARIANCE)
                status = ReconciliationStatus.MISMATCH
            elif abs_variance > 0:
                status = ReconciliationStatus.MATCHED_WITHIN_TOLERANCE
        date_left = l.data.get(request.date_field) if request.date_field else None
        date_right = r.data.get(request.date_field) if request.date_field else None
        if request.date_field and _date(date_left) and _date(date_right):
            if abs((_date(date_left) - _date(date_right)).days) > request.date_tolerance_days:
                reasons.append(ReasonCode.DATE_VARIANCE)
                status = ReconciliationStatus.MISMATCH
        currency_left = str(l.data.get(request.currency_field, "")).upper() if request.currency_field else None
        currency_right = str(r.data.get(request.currency_field, "")).upper() if request.currency_field else None
        if request.currency_field and currency_left and currency_right and currency_left != currency_right:
            reasons.append(ReasonCode.CURRENCY_MISMATCH)
            status = ReconciliationStatus.MISMATCH
        results.append(RecordMatch(
            left_record_id=l.record_id, right_record_id=r.record_id, status=status,
            reason_codes=list(dict.fromkeys(reasons)), amount_left=amount_left, amount_right=amount_right,
            amount_variance=variance, amount_variance_percent=variance_pct,
            date_left=str(date_left) if date_left is not None else None, date_right=str(date_right) if date_right is not None else None,
            currency_left=currency_left, currency_right=currency_right,
            materiality=_materiality(abs_variance, request.materiality_threshold), evidence=_evidence(l, r),
        ))

    total_abs = sum(abs(item.amount_variance or 0.0) for item in results)
    material = sum(item.materiality == "material" for item in results)
    summary = ReconciliationSummary(
        total_left=len(request.left_records), total_right=len(request.right_records),
        matched=sum(x.status == ReconciliationStatus.MATCHED for x in results),
        matched_within_tolerance=sum(x.status == ReconciliationStatus.MATCHED_WITHIN_TOLERANCE for x in results),
        mismatched=sum(x.status == ReconciliationStatus.MISMATCH for x in results),
        missing_left=sum(x.status == ReconciliationStatus.MISSING_LEFT for x in results),
        missing_right=sum(x.status == ReconciliationStatus.MISSING_RIGHT for x in results),
        duplicates=sum(x.status == ReconciliationStatus.DUPLICATE for x in results),
        review=sum(x.status == ReconciliationStatus.REVIEW for x in results),
        total_absolute_variance=total_abs, material_variance_count=material,
    )
    overall = "matched" if all(x.status in {ReconciliationStatus.MATCHED, ReconciliationStatus.MATCHED_WITHIN_TOLERANCE} for x in results) else "exceptions"
    return ReconciliationResult(status=overall, summary=summary, matches=results)
