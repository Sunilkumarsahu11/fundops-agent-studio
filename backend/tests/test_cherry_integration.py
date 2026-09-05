from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload() -> dict:
    return {
        "case_id": "PM-DEMO-001",
        "capital_call": {
            "fund_name": "Cedar Peak Growth Fund III LP",
            "investor_name": "Oakfield Pension Trust",
            "lp_reference": "LP-001",
            "notice_id": "NCGFIII-CALL-2026-03",
            "current_call": "1250000.00",
            "currency": "GBP",
            "due_date": "2026-09-06",
            "payment_reference": "NCGFIII-CALL-2026-03 / LP-001",
            "beneficiary": "Cedar Peak Growth Fund III LP",
        },
        "commitments": [
            {
                "lp_id": "LP-001",
                "lp_name": "Oakfield Pension Trust",
                "total_commitment": "5000000.00",
                "called_before_current": "2750000.00",
                "current_call": "1250000.00",
                "remaining_after_current": "1000000.00",
            }
        ],
        "approved_bank_details": [],
        "transactions": [
            {
                "transaction_id": "TXN-2026-0905-003",
                "booking_date": "2026-09-05",
                "direction": "credit",
                "amount": "1249500.00",
                "currency": "GBP",
                "counterparty": "Oakfield Pension Trust",
                "reference": "NCGFIII-CALL-2026-03 / LP-001",
                "description": "Capital contribution - Oakfield",
                "status": "BOOKED",
            }
        ],
        "cherry_analysis": {
            "matched_transaction_ids": ["TXN-2026-0905-003"],
            "findings": [
                {
                    "code": "cash.short_receipt",
                    "severity": "high",
                    "title": "Capital call is under-received",
                    "detail": "Matched cash is GBP 500 below the call amount.",
                }
            ],
        },
        "sources": [
            {"kind": "pdf", "file_name": "capital-call.pdf", "sha256": "pdfhash"},
            {"kind": "excel", "file_name": "commitments.xlsx", "sha256": "xlshash"},
            {"kind": "json", "file_name": "cash.json", "sha256": "jsonhash"},
        ],
    }


def test_cherry_capital_call_integration() -> None:
    response = client.post("/integration/cherry/capital-call", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "PM-DEMO-001"
    assert body["integration_version"] == "cherry-fundops-v1"
    assert body["capital_call_review"]["agent_id"] == "capital-call-review"
    assert body["reconciliation"]["agent_id"] == "fund-reconciliation"
    assert body["exception_investigation"]["agent_id"] == "exception-investigation"
    assert body["source_count"] == 3
    assert body["financial_boundary"].startswith("analysis-only")
