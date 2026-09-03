from fastapi import APIRouter, HTTPException

from app.fund_ops.library import FundOperationsLibrary
from app.fund_ops.models import AgentInput, AgentOutput, FundAgentSpec

router = APIRouter(prefix="/fund-ops", tags=["fund-ops"])
library = FundOperationsLibrary()


@router.get("/agents", response_model=list[FundAgentSpec])
def list_agents() -> list[FundAgentSpec]:
    return library.list()


@router.get("/agents/{agent_id}", response_model=FundAgentSpec)
def get_agent(agent_id: str) -> FundAgentSpec:
    agent = library.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="FundOps agent not found")
    return agent


@router.post("/agents/{agent_id}/run", response_model=AgentOutput)
def run_agent(agent_id: str, request: AgentInput) -> AgentOutput:
    if library.get(agent_id) is None:
        raise HTTPException(status_code=404, detail="FundOps agent not found")
    return library.execute(agent_id, request)
