from uuid import uuid4

from app.fund_ops.library import FundOperationsLibrary
from app.fund_ops.models import AgentInput
from app.fund_model.record import CanonicalRecord, Provenance


def record(record_id: str, data: dict) -> CanonicalRecord:
    return CanonicalRecord(
        record_id=uuid4(), model_id="private-markets", model_version=1,
        entity="Valuation", data=data,
        provenance=[Provenance(source_file=record_id)],
    )


def test_library_catalog_contains_core_fundops_agents():
    ids = {agent.id for agent in FundOperationsLibrary().list()}
    assert {"fund-reconciliation", "capital-call-review", "nav-review", "valuation-review", "investor-reporting", "fund-data-qa"} <= ids


def test_reconciliation_agent_uses_deterministic_engine_and_evidence():
    library = FundOperationsLibrary()
    result = library.execute("fund-reconciliation", AgentInput(
        parameters={
            "left_records": [record("admin.xlsx", {"id": "V1", "amount": 1000, "currency": "GBP"})],
            "right_records": [record("manager.xlsx", {"id": "V1", "amount": 1200, "currency": "GBP"})],
            "key_fields": ["id"], "amount_field": "amount", "currency_field": "currency", "materiality_threshold": 100,
        }
    ))
    assert result.status == "exceptions"
    assert result.result["exception_count"] == 1
    assert result.result["exceptions"][0]["evidence"]["left"]


def test_data_qa_does_not_fabricate_records():
    library = FundOperationsLibrary()
    result = library.execute("fund-data-qa", AgentInput(
        records=[record("fund.xlsx", {"fund_name": "Atlas Fund", "currency": "GBP"})],
        parameters={"question": "Atlas"},
    ))
    assert result.status == "completed"
    assert len(result.result["matches"]) == 1
