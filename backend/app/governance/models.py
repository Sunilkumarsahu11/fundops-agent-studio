from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    RUN_CREATED = "run_created"
    STEP_EXECUTED = "step_executed"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID | None = None
    agent_id: str | None = None
    action: AuditAction
    actor: str = "system"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    record_id: UUID | None = None
    entity: str | None = None
    source_file: str | None = None
    source_sheet: str | None = None
    source_cell: str | None = None
    source_path: str | None = None
    source_field: str | None = None
    excerpt: Any = None


class RunSnapshot(BaseModel):
    run_id: UUID
    agent_id: str
    agent_version: str = "1.0.0"
    request: dict[str, Any]
    output: dict[str, Any] = Field(default_factory=dict)
    status: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    action: str = Field(min_length=1)
    requested_by: str = Field(min_length=1)
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str | None = None
    decision_comment: str | None = None
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None


class ApprovalDecision(BaseModel):
    decided_by: str = Field(min_length=1)
    comment: str = ""
