from uuid import uuid4

import pytest

from app.agent_runtime.models import AgentDefinition, AgentRequest, AgentStatus, AgentRun, ExecutionEvent
from app.governance.models import ApprovalRequest, ApprovalStatus, AuditAction
from app.governance.service import GovernanceService


def test_capture_run_creates_immutable_audit_projection_and_snapshot():
    service = GovernanceService()
    agent = AgentDefinition(id="demo", name="Demo")
    run = AgentRun(agent_id="demo", request=AgentRequest(request="check"), status=AgentStatus.COMPLETED)
    event = ExecutionEvent(run_id=run.id, status=AgentStatus.COMPLETED, message="done")

    snapshot = service.capture_run(agent, run, [event])

    assert snapshot.run_id == run.id
    assert service.snapshots[run.id].status == "completed"
    assert [e.action for e in service.events_for_run(run.id)] == [AuditAction.RUN_CREATED, AuditAction.STEP_EXECUTED, AuditAction.RUN_COMPLETED]


def test_approval_requires_snapshot_and_cannot_be_decided_twice():
    service = GovernanceService()
    run_id = uuid4()
    with pytest.raises(KeyError):
        service.request_approval(ApprovalRequest(run_id=run_id, action="publish", requested_by="ops"))

    agent = AgentDefinition(id="demo", name="Demo")
    run = AgentRun(id=run_id, agent_id="demo", request=AgentRequest(request="check"), status=AgentStatus.COMPLETED)
    service.capture_run(agent, run, [])
    approval = service.request_approval(ApprovalRequest(run_id=run_id, action="publish", requested_by="ops"))
    decided = service.decide(approval.id, approved=True, decided_by="reviewer", comment="approved")

    assert decided.status == ApprovalStatus.APPROVED
    with pytest.raises(ValueError):
        service.decide(approval.id, approved=False, decided_by="reviewer", comment="late rejection")
