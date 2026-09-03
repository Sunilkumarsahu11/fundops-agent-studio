from app.agent_runtime.builtins import echo
from app.agent_runtime.models import AgentDefinition, AgentRequest, AgentStatus, WorkflowStep
from app.agent_runtime.registry import ToolRegistry
from app.agent_runtime.runtime import AgentRuntime


def build_runtime() -> AgentRuntime:
    registry = ToolRegistry()
    registry.register("echo", echo)
    return AgentRuntime(registry)


def test_runtime_executes_workflow() -> None:
    agent = AgentDefinition(
        id="demo-agent",
        name="Demo Agent",
        steps=[WorkflowStep(id="step-1", tool="echo")],
    )

    run = build_runtime().run(
        agent,
        AgentRequest(request="echo this", inputs={"value": 42}),
    )

    assert run.status == AgentStatus.COMPLETED
    assert run.context["step-1"]["received"]["value"] == 42
    assert run.errors == []


def test_runtime_fails_on_unknown_required_tool() -> None:
    agent = AgentDefinition(
        id="broken-agent",
        name="Broken Agent",
        steps=[WorkflowStep(id="step-1", tool="missing")],
    )

    run = build_runtime().run(agent, AgentRequest(request="run"))

    assert run.status == AgentStatus.FAILED
    assert "Unknown tool" in run.errors[0]
