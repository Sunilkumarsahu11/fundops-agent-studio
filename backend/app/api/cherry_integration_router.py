from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import get_settings
from app.fund_model.persistence import FundModelStore
from app.fund_model.records import CanonicalRecord, Provenance
from app.fund_ops.library import FundOperationsLibrary
from app.fund_ops.models import AgentInput

router = APIRouter(prefix="/integration/cherry", tags=["cherry-integration"])
settings = get_settings()
library = FundOperationsLibrary()
db_store = FundModelStore(settings.database_url)


class SourceDescriptor(BaseModel):
    kind: Literal["pdf", "excel", "json"]
    file_name: str
    sha256: str | None = None


class CherryCapitalCallCase(BaseModel):
    case_id: str = Field(min_length=3, max_length=160)
    capital_call: dict[str, Any]
    commitments: list[dict[str, Any]] = Field(default_factory=list)
    approved_bank_details: list[dict[str, Any]] = Field(default_factory=list)
    transactions: list[dict[str, Any]] = Field(default_factory=list)
    cherry_analysis: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceDescriptor] = Field(default_factory=list)


def _source_provenance(request: CherryCapitalCallCase, kind: str) -> list[Provenance]:
    return [
        Provenance(source_file=source.file_name, source_path=source.sha256)
        for source in request.sources
        if source.kind == kind
    ]


def _capital_call_record(request: CherryCapitalCallCase) -> CanonicalRecord:
    call = request.capital_call
    return CanonicalRecord(
        model_id="cherry-fundops-integration",
        model_version=1,
        entity="capital_call",
        data={
            "fund_id": call.get("fund_name") or "unknown-fund",
            "call_id": call.get("notice_id") or request.case_id,
            "lp_id": call.get("lp_reference") or call.get("investor_name") or "unknown-lp",
            "investor_name": call.get("investor_name"),
            "amount": call.get("current_call"),
            "currency": call.get("currency") or "GBP",
            "due_date": call.get("due_date"),
            "payment_reference": call.get("payment_reference"),
            "beneficiary": call.get("beneficiary"),
        },
        provenance=_source_provenance(request, "pdf"),
    )


def _cash_records(
    request: CherryCapitalCallCase,
    *,
    fund_id: str,
    call_id: str,
    lp_id: str,
) -> list[CanonicalRecord]:
    """Convert only Cherry's strongly matched cash into Agent Studio records.

    Cherry owns the strict cash-matching policy. If it supplied no matched transaction IDs,
    Agent Studio must not reinterpret unrelated fund cash as belonging to this capital call.
    """

    matched_ids = {
        str(value) for value in request.cherry_analysis.get("matched_transaction_ids", []) if value
    }
    if not matched_ids:
        return []

    provenance = _source_provenance(request, "json")
    records: list[CanonicalRecord] = []
    for transaction in request.transactions:
        transaction_id = str(transaction.get("transaction_id") or transaction.get("id") or "")
        if transaction_id not in matched_ids:
            continue
        records.append(
            CanonicalRecord(
                model_id="cherry-fundops-integration",
                model_version=1,
                entity="cash_transaction",
                data={
                    "fund_id": fund_id,
                    "call_id": call_id,
                    "lp_id": lp_id,
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency") or "GBP",
                    "date": transaction.get("booking_date"),
                    "transaction_id": transaction_id,
                    "reference": transaction.get("reference"),
                    "counterparty": transaction.get("counterparty"),
                },
                provenance=provenance,
            )
        )
    return records


def _collect_exceptions(
    request: CherryCapitalCallCase,
    capital_call_review: dict[str, Any],
    reconciliation: dict[str, Any],
) -> list[dict[str, Any]]:
    exceptions: list[dict[str, Any]] = []
    for finding in request.cherry_analysis.get("findings", []):
        severity = str(finding.get("severity", "warning")).lower()
        if severity not in {"high", "warning"}:
            continue
        exceptions.append(
            {
                "code": finding.get("code", "CHERRY_CONTROL"),
                "severity": "high" if severity == "high" else "medium",
                "message": finding.get("detail")
                or finding.get("title")
                or "Cherry control finding",
                "source": "cherry-strict-controls",
            }
        )

    review_result = capital_call_review.get("result", {})
    for item in review_result.get("exceptions", []):
        exceptions.append(
            {
                **item,
                "severity": item.get("severity", "high"),
                "source": "agent-studio-capital-call-review",
            }
        )

    report = reconciliation.get("result", {}).get("report", {})
    for item in report.get("exceptions", []):
        exceptions.append(
            {
                **item,
                "severity": item.get("severity", "high"),
                "source": "agent-studio-reconciliation",
            }
        )
    return exceptions


@router.get("/health")
def health() -> dict[str, Any]:
    database_ready = False
    try:
        with db_store.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ready = True
    except Exception:
        database_ready = False
    return {
        "status": "ok",
        "service": "fundops-agent-studio",
        "integration": "cherry-fundops-v1",
        "database_ready": database_ready,
        "database_backend": db_store.engine.dialect.name,
        "accepted_upstream_inputs": ["pdf", "excel", "json"],
        "financial_boundary": "analysis-only; no payment initiation",
    }


@router.post("/capital-call")
def capital_call(request: CherryCapitalCallCase) -> dict[str, Any]:
    call_record = _capital_call_record(request)
    capital_call_review = library.execute(
        "capital-call-review",
        AgentInput(
            records=[call_record],
            parameters={
                "required_fields": ["fund_id", "call_id", "lp_id", "amount", "currency"],
                "amount_field": "amount",
                "id_fields": ["fund_id", "call_id", "lp_id"],
            },
        ),
    ).model_dump(mode="json")

    fund_id = str(call_record.data["fund_id"])
    call_id = str(call_record.data["call_id"])
    lp_id = str(call_record.data["lp_id"])
    expected_record = CanonicalRecord(
        model_id="cherry-fundops-integration",
        model_version=1,
        entity="expected_cash",
        data={
            "fund_id": fund_id,
            "call_id": call_id,
            "lp_id": lp_id,
            "amount": call_record.data.get("amount"),
            "currency": call_record.data.get("currency"),
            "date": call_record.data.get("due_date"),
        },
        provenance=(
            _source_provenance(request, "excel") or _source_provenance(request, "pdf")
        ),
    )
    actual_records = _cash_records(
        request,
        fund_id=fund_id,
        call_id=call_id,
        lp_id=lp_id,
    )
    reconciliation = library.execute(
        "fund-reconciliation",
        AgentInput(
            parameters={
                "left_records": [expected_record.model_dump(mode="json")],
                "right_records": [record.model_dump(mode="json") for record in actual_records],
                "key_fields": ["fund_id", "call_id", "lp_id"],
                "amount_field": "amount",
                "date_field": "date",
                "currency_field": "currency",
                "amount_tolerance": 0.0,
                "amount_tolerance_percent": 0.0,
                "date_tolerance_days": 10,
                "materiality_threshold": 0.0,
            }
        ),
    ).model_dump(mode="json")

    exceptions = _collect_exceptions(request, capital_call_review, reconciliation)
    investigation = library.execute(
        "exception-investigation",
        AgentInput(parameters={"exceptions": exceptions, "default_severity": "medium"}),
    ).model_dump(mode="json")

    return {
        "case_id": request.case_id,
        "service": "fundops-agent-studio",
        "integration_version": "cherry-fundops-v1",
        "capital_call_review": capital_call_review,
        "reconciliation": reconciliation,
        "exception_investigation": investigation,
        "canonical_records": {
            "capital_call": call_record.model_dump(mode="json"),
            "expected_cash": expected_record.model_dump(mode="json"),
            "matched_cash": [record.model_dump(mode="json") for record in actual_records],
        },
        "source_count": len(request.sources),
        "database": {
            "backend": db_store.engine.dialect.name,
            "configured_url": bool(settings.database_url),
        },
        "financial_boundary": "analysis-only; Cherry FundOps retains the control decision",
    }
