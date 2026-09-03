from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.agent_runtime.models import WorkflowStep


class BlueprintStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    PUBLISHED = "published"


class FactoryRequest(BaseModel):
    request: str = Field(min_length=5)
    name: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


class ToolSelection(BaseModel):
    tool: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class AgentBlueprint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    source_request: str
    status: BlueprintStatus = BlueprintStatus.DRAFT
    tools: list[ToolSelection] = Field(default_factory=list)
    steps: list[WorkflowStep] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactoryValidation(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PublishRequest(BaseModel):
    approved_by: str = Field(min_length=1)


class PublishResult(BaseModel):
    blueprint: AgentBlueprint
    agent_id: str
    published: bool
