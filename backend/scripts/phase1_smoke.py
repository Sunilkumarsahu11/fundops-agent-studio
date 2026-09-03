from app.agent_runtime.builtins import register_builtins
from app.agent_runtime.models import AgentDefinition, AgentRequest, WorkflowStep
from app.agent_runtime.registry import ToolRegistry
from app.agent_runtime.runtime import AgentRuntime


if __name__ == "__main__":
    registry = ToolRegistry()
    register_builtins(registry)
    runtime = AgentRuntime(registry)
    agent = AgentDefinition(
        id="phase1-smoke",
        name="Phase 1 Smoke Agent",
        steps=[WorkflowStep(id="echo", tool="echo")],
    )
    run = runtime.run(agent, AgentRequest(request="smoke test", inputs={"hello": "fundops"}))
    print(run.model_dump_json(indent=2))
