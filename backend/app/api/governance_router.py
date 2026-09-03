from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.governance.models import ApprovalDecision, ApprovalRequest
from app.governance.service import GovernanceService

router = APIRouter(prefix="/governance", tags=["governance"])
service = GovernanceService()


@router.get("/runs/{run_id}/audit")
def get_audit(run_id: UUID):
    return [event.model_dump(mode="json") for event in service.events_for_run(run_id)]


@router.get("/runs/{run_id}/evidence")
def get_evidence(run_id: UUID):
    return [item.model_dump(mode="json") for item in service.evidence_for_run(run_id)]


@router.get("/runs/{run_id}/snapshot")
def get_snapshot(run_id: UUID):
    snapshot = service.snapshots.get(run_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Run snapshot not found")
    return snapshot


@router.post("/approvals", response_model=ApprovalRequest)
def create_approval(request: ApprovalRequest) -> ApprovalRequest:
    try:
        return service.request_approval(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/approvals/{approval_id}", response_model=ApprovalRequest)
def get_approval(approval_id: UUID) -> ApprovalRequest:
    approval = service.approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalRequest)
def approve(approval_id: UUID, decision: ApprovalDecision) -> ApprovalRequest:
    try:
        return service.decide(approval_id, approved=True, decided_by=decision.decided_by, comment=decision.comment)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalRequest)
def reject(approval_id: UUID, decision: ApprovalDecision) -> ApprovalRequest:
    try:
        return service.decide(approval_id, approved=False, decided_by=decision.decided_by, comment=decision.comment)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
