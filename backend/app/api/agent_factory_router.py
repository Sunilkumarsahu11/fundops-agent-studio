from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent_runtime.container import registry
from app.agent_runtime.models import AgentDefinition
from app.agent_factory.factory import AgentFactory
from app.agent_factory.llm import LLMPlanner, LLMUnavailableError
from app.agent_factory.models import AgentBlueprint, FactoryRequest, FactoryValidation, PublishRequest, PublishResult

router = APIRouter(prefix="/agent-factory", tags=["agent-factory"])
factory = AgentFactory(registry)
llm_planner = LLMPlanner(registry)

TEMPLATES = [
    {"id": "fund-reconciliation", "name": "Fund Reconciliation", "request": "Reconcile administrator valuation workbook against manager valuation workbook and flag material exceptions"},
    {"id": "source-inspection", "name": "Source Inspection", "request": "Inspect a fund operations workbook before importing it"},
]


class LLMExplainRequest(BaseModel):
    request: str = Field(min_length=5)
    result: dict[str, Any]


@router.get("/templates")
def templates() -> list[dict[str, str]]:
    return TEMPLATES


@router.get("/llm/status")
def llm_status() -> dict[str, Any]:
    return {"configured": llm_planner.configured, "model": llm_planner.model or None, "planner": "langchain-llm"}


@router.post("/draft", response_model=AgentBlueprint)
def draft(request: FactoryRequest) -> AgentBlueprint:
    return factory.draft(request)


@router.post("/draft-llm", response_model=AgentBlueprint)
def draft_llm(request: FactoryRequest) -> AgentBlueprint:
    try:
        return llm_planner.plan(request)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/explain")
def explain(request: LLMExplainRequest) -> dict[str, str | None]:
    try:
        return {"explanation": llm_planner.explain(request.request, request.result), "model": llm_planner.model or None}
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
