from collections.abc import Callable
from time import sleep
from typing import Any

from .models import (
    AgentDefinition,
    AgentRequest,
    AgentRun,
    AgentStatus,
    ExecutionEvent,
    ValidationResult,
)
from .registry import ToolRegistry

Validator = Callable[[AgentRun], ValidationResult]


class AgentRuntime:
    """Synchronous runtime with retries, event history and validation hooks."""

    def __init__(self, registry: ToolRegistry, validators: list[Validator] | None = None) -> None:
        self.registry = registry
        self.validators = validators or []
        self._events: dict[str, list[ExecutionEvent]] = {}

    def events(self, run_id: str) -> list[ExecutionEvent]:
        return list(self._events.get(run_id, []))

    def run(
        self,
        agent: AgentDefinition,
        request: AgentRequest,
        on_event: Callable[[ExecutionEvent], None] | None = None,
    ) -> AgentRun:
        run = AgentRun(agent_id=agent.id, request=request)
        self._events[str(run.id)] = []

        def emit(status: AgentStatus, message: str, step_id: str | None = None, attempt: int | None = None) -> None:
            run.status = status
            event = ExecutionEvent(run_id=run.id, status=status, message=message, step_id=step_id, attempt=attempt)
            self._events[str(run.id)].append(event)
            if on_event:
                on_event(event)

        try:
            emit(AgentStatus.UNDERSTANDING, "Request accepted")
            run.context.update(request.inputs)
            emit(AgentStatus.PLANNING, "Workflow loaded")
            if not agent.steps:
                raise ValueError("Agent has no workflow steps")

            emit(AgentStatus.EXECUTING, "Executing workflow")
            for step in agent.steps:
                if not self.registry.has(step.tool):
                    if step.required:
                        raise RuntimeError(f"Step '{step.id}' failed: Unknown tool: {step.tool}")
                    continue
                policy = step.retry_policy
                result = None
                for attempt in range(1, policy.max_attempts + 1):
                    emit(AgentStatus.EXECUTING, f"Executing step {step.id}", step.id, attempt)
                    result = self.registry.execute(step.tool, {**run.context, **step.input})
                    if result.success or not policy.retryable or attempt == policy.max_attempts:
                        break
                    if policy.backoff_seconds:
                        sleep(policy.backoff_seconds * attempt)
                assert result is not None
                if not result.success:
                    if step.required:
                        raise RuntimeError(f"Step '{step.id}' failed after {policy.max_attempts} attempt(s): {result.error}")
                    continue
                run.context[step.id] = result.output

            emit(AgentStatus.VALIDATING, "Validating execution result")
            validation_errors: list[str] = []
            for validator in self.validators:
                validation = validator(run)
                validation_errors.extend(validation.errors)
            if validation_errors:
                raise RuntimeError("Validation failed: " + "; ".join(validation_errors))

            emit(AgentStatus.EXPLAINING, "Preparing execution summary")
            run.output = {"context": run.context, "event_count": len(self._events[str(run.id)])}
            emit(AgentStatus.COMPLETED, "Agent run completed")
            return run
        except Exception as exc:  # noqa: BLE001 - runtime boundary
            run.errors.append(str(exc))
            emit(AgentStatus.FAILED, str(exc))
            return run
