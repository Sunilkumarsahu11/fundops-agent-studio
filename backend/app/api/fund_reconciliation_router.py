from fastapi import APIRouter

from app.reconciliation.agent import FundReconciliationAgent
from app.reconciliation.models import ReconciliationRequest, ReconciliationResult
from app.reconciliation.report import build_exception_report

router = APIRouter(prefix="/fund-reconciliation", tags=["fund-reconciliation"])
agent = FundReconciliationAgent()


@router.post("/run", response_model=ReconciliationResult)
def run(request: ReconciliationRequest) -> ReconciliationResult:
    return reconcile_request(request)


def reconcile_request(request: ReconciliationRequest) -> ReconciliationResult:
    result = agent.run(
        request.left_records,
        request.right_records,
        key_fields=request.key_fields,
        amount_field=request.amount_field,
        date_field=request.date_field,
        currency_field=request.currency_field,
        amount_tolerance=request.amount_tolerance,
        amount_tolerance_percent=request.amount_tolerance_percent,
        date_tolerance_days=request.date_tolerance_days,
        materiality_threshold=request.materiality_threshold,
    )[0]
    return result


@router.post("/report")
def report(request: ReconciliationRequest):
    result = reconcile_request(request)
    return build_exception_report(result)
