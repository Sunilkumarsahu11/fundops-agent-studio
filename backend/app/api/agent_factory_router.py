from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.agent_runtime.builtins import register_builtins
from app.agent_runtime.models import AgentDefinition, ToolDefinition
from app.agent_runtime.registry import ToolRegistry
from app.agent_factory.factory import AgentFactory
from app.agent_factory.models import AgentBlueprint, FactoryRequest, FactoryValidation, PublishRequest, PublishResult

router = APIRouter(prefix="/agent-factory", tags=["agent-factory"])
registry = ToolRegistry()
register_builtins(registry)
factory = AgentFactory(registry)

TEMPLATES = [
    {"id": "fund-reconciliation", "name": "Fund Reconciliation", "request": "Reconcile administrator valuation workbook against manager valuation workbook and flag material exceptions"},
    {"id": "source-inspection", "name": "Source Inspection", "request": "Inspect a fund operations workbook before importing it"},
]

@router.get("/templates")
def templates() -> list[dict[str, str]]:
    return TEMPLATES

@router.post("/draft", response_model=AgentBlueprint)
def draft(request: FactoryRequest) -> AgentBlueprint:
    return factory.draft(request)

@router.post("/validate", response_model=FactoryValidation)
def validate(blueprint: AgentBlueprint) -> FactoryValidation:
    return factory.validate(blueprint)

@router.post("/publish/{blueprint_id}", response_model=PublishResult)
def publish(blueprint_id: UUID, request: PublishRequest) -> PublishResult:
    blueprint = factory.get(str(blueprint_id))
    if blueprint is None:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    validation = factory.validate(blueprint)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)
    agent: AgentDefinition = factory.publish(blueprint, request.approved_by)
    return PublishResult(blueprint=blueprint, agent_id=agent.id, published=True)
