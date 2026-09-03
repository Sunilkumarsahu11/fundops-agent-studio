from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.agent_runtime.builtins import register_builtins
from app.agent_runtime.models import AgentDefinition, AgentRequest, AgentRun, ToolDefinition
from app.agent_runtime.registry import ToolRegistry
from app.agent_runtime.runtime import AgentRuntime
from app.agent_runtime.store import InMemoryAgentStore
from app.api.fund_model_router import router as fund_model_router
from app.api.ingestion_router import router as ingestion_router
from app.api.reconciliation_router import router as reconciliation_router

router = APIRouter()
store = InMemoryAgentStore()
registry = ToolRegistry()
register_builtins(registry)
runtime = AgentRuntime(registry)
router.include_router(fund_model_router)
router.include_router(ingestion_router)
router.include_router(reconciliation_router)


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fundops-agent-studio"}


@router.get("/tools", response_model=list[ToolDefinition], tags=["runtime"])
def list_tools() -> list[ToolDefinition]:
    return registry.definitions()


@router.get("/agents", response_model=list[AgentDefinition], tags=["agents"])
def list_agents() -> list[AgentDefinition]:
    return store.list_agents()


@router.post("/agents", response_model=AgentDefinition, tags=["agents"])
def create_agent(agent: AgentDefinition) -> AgentDefinition:
    for step in agent.steps:
        if not registry.has(step.tool):
            raise HTTPException(status_code=400, detail=f"Unknown tool: {step.tool}")
    return store.save_agent(agent)


@router.get("/agents/{agent_id}", response_model=AgentDefinition, tags=["agents"])
def get_agent(agent_id: str) -> AgentDefinition:
    agent = store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/agents/{agent_id}/run", response_model=AgentRun, tags=["runs"])
def run_agent(agent_id: str, request: AgentRequest) -> AgentRun:
    agent = store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    run = runtime.run(agent, request)
    return store.save_run(run)


@router.get("/runs/{run_id}", response_model=AgentRun, tags=["runs"])
def get_run(run_id: UUID) -> AgentRun:
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/events", tags=["runs"])
def get_run_events(run_id: UUID) -> list[dict]:
    if store.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return [event.model_dump(mode="json") for event in runtime.events(str(run_id))]
