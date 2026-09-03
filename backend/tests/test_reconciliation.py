from datetime import datetime, timezone

from app.fund_model.records import CanonicalRecord, Provenance
from app.reconciliation.engine import reconcile
from app.reconciliation.models import ReconciliationRequest, ReconciliationStatus, ReasonCode


def record(record_id: str, data: dict, source: str) -> CanonicalRecord:
    return CanonicalRecord(
        record_id=record_id,
        model_id="private-markets",
        model_version=1,
        entity="Valuation",
        data=data,
        provenance=[Provenance(source_file=source, source_sheet="Valuations", source_cell="A2")],
        created_at=datetime.now(timezone.utc),
    )


def test_exact_match():
    result = reconcile(ReconciliationRequest(
        left_records=[record("00000000-0000-0000-0000-000000000001", {"valuation_id": "V1", "value": 100, "currency": "GBP"}, "a.xlsx")],
        right_records=[record("00000000-0000-0000-0000-000000000002", {"valuation_id": "V1", "value": 100, "currency": "GBP"}, "b.xlsx")],
        key_fields=["valuation_id"], amount_field="value", currency_field="currency",
    ))
    assert result.status == "matched"
    assert result.summary.matched == 1
    assert result.matches[0].reason_codes == [ReasonCode.EXACT_MATCH]


def test_amount_tolerance_and_materiality():
    result = reconcile(ReconciliationRequest(
        left_records=[record("00000000-0000-0000-0000-000000000003", {"id": "V1", "amount": 1000}, "a.xlsx")],
        right_records=[record("00000000-0000-0000-0000-000000000004", {"id": "V1", "amount": 1002}, "b.xlsx")],
        key_fields=["id"], amount_field="amount", amount_tolerance=5, materiality_threshold=1,
    ))
    assert result.matches[0].status == ReconciliationStatus.MATCHED_WITHIN_TOLERANCE
    assert result.matches[0].materiality == "material"


def test_detects_missing_and_currency_mismatch():
    result = reconcile(ReconciliationRequest(
        left_records=[record("00000000-0000-0000-0000-000000000005", {"id": "V1", "amount": 100, "ccy": "GBP"}, "a.xlsx")],
        right_records=[record("00000000-0000-0000-0000-000000000006", {"id": "V2", "amount": 100, "ccy": "GBP"}, "b.xlsx"), record("00000000-0000-0000-0000-000000000007", {"id": "V1", "amount": 100, "ccy": "USD"}, "b.xlsx")],
        key_fields=["id"], amount_field="amount", currency_field="ccy",
    ))
    assert result.summary.missing_left == 1
    assert any(ReasonCode.CURRENCY_MISMATCH in item.reason_codes for item in result.matches)


def test_detects_duplicates():
    result = reconcile(ReconciliationRequest(
        left_records=[record("00000000-0000-0000-0000-000000000008", {"id": "V1", "amount": 100}, "a.xlsx"), record("00000000-0000-0000-0000-000000000009", {"id": "V1", "amount": 100}, "a.xlsx")],
        right_records=[record("00000000-0000-0000-0000-000000000010", {"id": "V1", "amount": 100}, "b.xlsx")],
        key_fields=["id"], amount_field="amount",
    ))
    assert result.summary.duplicates == 3
