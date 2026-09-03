from typing import Protocol

from .models import AgentDefinition, AgentRequest, ToolDefinition, WorkflowStep


class Planner(Protocol):
    def plan(
        self,
        request: AgentRequest,
        agent: AgentDefinition,
        tools: list[ToolDefinition],
    ) -> list[WorkflowStep]: ...


class StaticPlanner:
    """Phase 1 planner; Phase 10 can replace this with an LLM planner."""

    def plan(
        self,
        request: AgentRequest,
        agent: AgentDefinition,
        tools: list[ToolDefinition],
    ) -> list[WorkflowStep]:
        del request, tools
        return agent.steps
