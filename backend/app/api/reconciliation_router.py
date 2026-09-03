from fastapi import APIRouter

from app.reconciliation.engine import reconcile
from app.reconciliation.models import ReconciliationRequest, ReconciliationResult

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/run", response_model=ReconciliationResult)
def run_reconciliation(request: ReconciliationRequest) -> ReconciliationResult:
    return reconcile(request)
