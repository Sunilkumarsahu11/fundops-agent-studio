from datetime import datetime, timezone

from app.fund_model.records import CanonicalRecord, Provenance
from app.reconciliation.agent import FundReconciliationAgent


def make_record(record_id: str, data: dict, source: str) -> CanonicalRecord:
    return CanonicalRecord(
        record_id=record_id,
        model_id="private-markets",
        model_version=1,
        entity="Valuation",
        data=data,
        provenance=[Provenance(source_file=source, source_sheet="Valuations", source_cell="B2")],
        created_at=datetime.now(timezone.utc),
    )


def test_agent_produces_evidence_backed_exception_report():
    left = [make_record("10000000-0000-0000-0000-000000000001", {"id": "V1", "amount": 1000, "currency": "GBP"}, "administrator.xlsx")]
    right = [make_record("10000000-0000-0000-0000-000000000002", {"id": "V1", "amount": 1200, "currency": "GBP"}, "manager.xlsx")]
    result, report = FundReconciliationAgent().run(
        left, right, key_fields=["id"], amount_field="amount", currency_field="currency", materiality_threshold=100,
    )
    assert result.status == "exceptions"
    assert report["exception_count"] == 1
    assert report["exceptions"][0]["evidence"]["left"]
    assert report["exceptions"][0]["evidence"]["right"]
