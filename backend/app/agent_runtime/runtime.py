from collections.abc import Callable
from typing import Any

from .models import AgentDefinition, AgentRequest, AgentRun, AgentStatus, ExecutionEvent
from .registry import ToolRegistry


class AgentRuntime:
    """Minimal synchronous runtime for executing declarative agent workflows."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def run(
        self,
        agent: AgentDefinition,
        request: AgentRequest,
        on_event: Callable[[ExecutionEvent], None] | None = None,
    ) -> AgentRun:
        run = AgentRun(agent_id=agent.id, request=request)

        def emit(status: AgentStatus, message: str, step_id: str | None = None) -> None:
            run.status = status
            if on_event:
                on_event(ExecutionEvent(run_id=run.id, status=status, message=message, step_id=step_id))

        try:
            emit(AgentStatus.UNDERSTANDING, "Request accepted")
            run.context.update(request.inputs)

            emit(AgentStatus.PLANNING, "Workflow loaded")
            if not agent.steps:
                raise ValueError("Agent has no workflow steps")

            emit(AgentStatus.EXECUTING, "Executing workflow")
            for step in agent.steps:
                result = self.registry.execute(step.tool, {**run.context, **step.input})
                if not result.success:
                    if step.required:
                        raise RuntimeError(f"Step '{step.id}' failed: {result.error}")
                    continue
                run.context[step.id] = result.output

            emit(AgentStatus.VALIDATING, "Workflow completed; validating result")
            emit(AgentStatus.EXPLAINING, "Preparing execution summary")
            run.output = {"context": run.context}
            emit(AgentStatus.COMPLETED, "Agent run completed")
            return run
        except Exception as exc:  # noqa: BLE001 - runtime boundary
            run.errors.append(str(exc))
            emit(AgentStatus.FAILED, str(exc))
            return run
