from uuid import UUID

from .models import AgentDefinition, AgentRun


class InMemoryAgentStore:
    """Phase 1 persistence boundary; replace implementation with PostgreSQL in Phase 2."""

    def __init__(self) -> None:
        self.agents: dict[str, AgentDefinition] = {}
        self.runs: dict[UUID, AgentRun] = {}

    def save_agent(self, agent: AgentDefinition) -> AgentDefinition:
        self.agents[agent.id] = agent
        return agent

    def get_agent(self, agent_id: str) -> AgentDefinition | None:
        return self.agents.get(agent_id)

    def list_agents(self) -> list[AgentDefinition]:
        return list(self.agents.values())

    def save_run(self, run: AgentRun) -> AgentRun:
        self.runs[run.id] = run
        return run

    def get_run(self, run_id: UUID) -> AgentRun | None:
        return self.runs.get(run_id)
