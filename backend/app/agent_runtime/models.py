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


class WorkflowStep(BaseModel):
    id: str
    tool: str
    input: dict[str, Any] = Field(default_factory=dict)
    required: bool = True


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


class ToolResult(BaseModel):
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ExecutionEvent(BaseModel):
    run_id: UUID
    status: AgentStatus
    message: str
    step_id: str | None = None
