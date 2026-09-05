import io
from uuid import uuid4

from openpyxl import Workbook

from app.fund_model.records import CanonicalRecord, Provenance
from app.fund_ops.library import FundOperationsLibrary
from app.fund_ops.models import AgentInput


def record(record_id: str, data: dict) -> CanonicalRecord:
    return CanonicalRecord(
        record_id=uuid4(),
        model_id="private-markets",
        model_version=1,
        entity="Valuation",
        data=data,
        provenance=[Provenance(source_file=record_id)],
    )


def test_library_catalog_contains_all_agents():
    ids = {agent.id for agent in FundOperationsLibrary().list()}
    assert ids == {
        "fund-reconciliation",
        "excel-quality",
        "capital-call-review",
        "nav-review",
        "valuation-review",
        "normalization",
        "portfolio-exposure",
        "investor-reporting",
        "exception-investigation",
        "fund-data-qa",
    }


def test_reconciliation_agent_uses_deterministic_engine_and_evidence():
    library = FundOperationsLibrary()
    result = library.execute(
        "fund-reconciliation",
        AgentInput(
            parameters={
                "left_records": [
                    record(
                        "admin.xlsx",
                        {"id": "V1", "amount": 1000, "currency": "GBP"},
                    )
                ],
                "right_records": [
                    record(
                        "manager.xlsx",
                        {"id": "V1", "amount": 1200, "currency": "GBP"},
                    )
                ],
                "key_fields": ["id"],
                "amount_field": "amount",
                "currency_field": "currency",
                "materiality_threshold": 100,
            }
        ),
    )
    assert result.status == "exceptions"
    report = result.result["report"]
    assert report["exception_count"] == 1
    assert report["exceptions"][0]["evidence"]["left"]


def test_excel_quality_agent_executes_shared_tool():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Valuations"
    sheet.append(["fund_id", "amount", "unused"])
    sheet.append(["F1", 1000, None])
    buffer = io.BytesIO()
    workbook.save(buffer)
    result = FundOperationsLibrary().execute(
        "excel-quality",
        AgentInput(
            parameters={
                "file_name": "quality.xlsx",
                "content_base64": __import__("base64")
                .b64encode(buffer.getvalue())
                .decode(),
            }
        ),
    )
    assert result.status == "issues"
    assert result.result["issue_count"] == 1
    assert result.result["issues"][0]["code"] == "BLANK_COLUMNS"


def test_exception_investigation_agent_executes_shared_tool():
    result = FundOperationsLibrary().execute(
        "exception-investigation",
        AgentInput(
            parameters={
                "exceptions": [
                    {"record_id": "2", "code": "MISSING_NAV", "severity": "high"},
                    {
                        "record_id": "1",
                        "code": "DATE_VARIANCE",
                        "severity": "critical",
                    },
                ]
            }
        ),
    )
    assert result.status == "exceptions"
    assert [item["severity"] for item in result.result["exceptions"]] == [
        "critical",
        "high",
    ]


def test_data_qa_does_not_fabricate_records():
    result = FundOperationsLibrary().execute(
        "fund-data-qa",
        AgentInput(
            records=[
                record("fund.xlsx", {"fund_name": "Atlas Fund", "currency": "GBP"})
            ],
            parameters={"question": "Atlas"},
        ),
    )
    assert result.status == "completed"
    assert len(result.result["records"]) == 1
