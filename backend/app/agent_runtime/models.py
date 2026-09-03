from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    RECEIVED = "received"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    EXPLAINING = "explaining"
    COMPLETED = "completed"
    FAILED = "failed"


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=1, ge=1, le=10)
    backoff_seconds: float = Field(default=0.0, ge=0.0, le=60.0)
    retryable: bool = True


class WorkflowStep(BaseModel):
    id: str
    tool: str
    input: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)


class AgentDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    steps: list[WorkflowStep] = Field(default_factory=list)


class AgentRequest(BaseModel):
    request: str
    inputs: dict[str, Any] = Field(default_factory=dict)


class AgentRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent_id: str
    request: AgentRequest
    status: AgentStatus = AgentStatus.RECEIVED
    context: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    deterministic: bool = True
    version: str = "1.0.0"
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class ToolResult(BaseModel):
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    attempts: int = 1


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExecutionEvent(BaseModel):
    run_id: UUID
    status: AgentStatus
    message: str
    step_id: str | None = None
    attempt: int | None = None
