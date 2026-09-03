from typing import Any
from uuid import UUID

from app.agent_runtime.models import AgentDefinition, AgentRun, ExecutionEvent

from .models import ApprovalRequest, ApprovalStatus, AuditAction, AuditEvent, EvidenceItem, RunSnapshot


class GovernanceService:
    """In-memory governance boundary; persistence can be swapped for PostgreSQL later."""

    def __init__(self) -> None:
        self.audit_events: list[AuditEvent] = []
        self.evidence: dict[UUID, EvidenceItem] = {}
        self.snapshots: dict[UUID, RunSnapshot] = {}
        self.approvals: dict[UUID, ApprovalRequest] = {}

    def record_event(self, event: AuditEvent) -> AuditEvent:
        self.audit_events.append(event)
        return event

    def capture_run(self, agent: AgentDefinition, run: AgentRun, events: list[ExecutionEvent]) -> RunSnapshot:
        self.record_event(AuditEvent(run_id=run.id, agent_id=agent.id, action=AuditAction.RUN_CREATED, message="Run snapshot captured"))
        for event in events:
            action = AuditAction.RUN_FAILED if event.status.value == "failed" else AuditAction.STEP_EXECUTED
            self.record_event(AuditEvent(
                run_id=run.id,
                agent_id=agent.id,
                action=action,
                message=event.message,
                details=event.model_dump(mode="json"),
            ))
        final_action = AuditAction.RUN_COMPLETED if run.status.value == "completed" else AuditAction.RUN_FAILED
        self.record_event(AuditEvent(run_id=run.id, agent_id=agent.id, action=final_action, message=f"Run {run.status.value}"))
        snapshot = RunSnapshot(
            run_id=run.id,
            agent_id=agent.id,
            agent_version="1.0.0",
            request=run.request.model_dump(mode="json"),
            output=run.output,
            status=run.status.value,
        )
        self.snapshots[run.id] = snapshot
        self._extract_evidence(run.id, run.output)
        return snapshot

    def _extract_evidence(self, run_id: UUID, value: Any) -> None:
        if isinstance(value, dict):
            provenance = value.get("provenance")
            if isinstance(provenance, list):
                record_id = None
                raw_id = value.get("record_id")
                try:
                    record_id = UUID(str(raw_id)) if raw_id else None
                except ValueError:
                    pass
                for item in provenance:
                    if isinstance(item, dict):
                        evidence = EvidenceItem(run_id=run_id, record_id=record_id, **{
                            key: item.get(key) for key in ("source_file", "source_sheet", "source_cell", "source_path", "source_field")
                        })
                        self.evidence[evidence.id] = evidence
            for child in value.values():
                self._extract_evidence(run_id, child)
        elif isinstance(value, list):
            for child in value:
                self._extract_evidence(run_id, child)

    def events_for_run(self, run_id: UUID) -> list[AuditEvent]:
        return [event for event in self.audit_events if event.run_id == run_id]

    def evidence_for_run(self, run_id: UUID) -> list[EvidenceItem]:
        return [item for item in self.evidence.values() if item.run_id == run_id]

    def request_approval(self, request: ApprovalRequest) -> ApprovalRequest:
        if request.run_id not in self.snapshots:
            raise KeyError("Run snapshot not found")
        self.approvals[request.id] = request
        self.record_event(AuditEvent(run_id=request.run_id, action=AuditAction.APPROVAL_REQUESTED, actor=request.requested_by, message=f"Approval requested for {request.action}", details={"approval_id": str(request.id)}))
        return request

    def decide(self, approval_id: UUID, *, approved: bool, decided_by: str, comment: str) -> ApprovalRequest:
        approval = self.approvals.get(approval_id)
        if approval is None:
            raise KeyError("Approval not found")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError("Approval has already been decided")
        from datetime import datetime, timezone
        approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval.decided_by = decided_by
        approval.decision_comment = comment
        approval.decided_at = datetime.now(timezone.utc)
        action = AuditAction.APPROVED if approved else AuditAction.REJECTED
        self.record_event(AuditEvent(run_id=approval.run_id, action=action, actor=decided_by, message=f"Approval {approval.status.value}", details={"approval_id": str(approval.id), "action": approval.action}))
        return approval
