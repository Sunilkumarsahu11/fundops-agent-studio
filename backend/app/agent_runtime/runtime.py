from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from time import sleep
from typing import Any

from .models import AgentDefinition, AgentRequest, AgentRun, AgentStatus, ExecutionEvent, ToolResult, ValidationResult
from .planner import Planner, StaticPlanner
from .registry import ToolRegistry

Validator = Callable[[AgentRun], ValidationResult]


class AgentRuntime:
    """Synchronous runtime with planning, retries, timeouts, events and validation hooks."""

    def __init__(self, registry: ToolRegistry, planner: Planner | None = None, validators: list[Validator] | None = None) -> None:
        self.registry = registry
        self.planner = planner or StaticPlanner()
        self.validators = validators or []
        self._events: dict[str, list[ExecutionEvent]] = {}

    def events(self, run_id: str) -> list[ExecutionEvent]:
        return list(self._events.get(run_id, []))

    def _execute_with_timeout(self, tool: str, inputs: dict, timeout_seconds: float) -> ToolResult:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.registry.execute, tool, inputs)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            future.cancel()
            return ToolResult(success=False, error=f"Tool '{tool}' timed out after {timeout_seconds}s")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _resolve(value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$") and value[1:] in context:
            return context[value[1:]]
        if isinstance(value, dict):
            return {key: AgentRuntime._resolve(item, context) for key, item in value.items()}
        if isinstance(value, list):
            return [AgentRuntime._resolve(item, context) for item in value]
        return value

    def run(self, agent: AgentDefinition, request: AgentRequest, on_event: Callable[[ExecutionEvent], None] | None = None) -> AgentRun:
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
            emit(AgentStatus.PLANNING, "Building execution plan")
            steps = self.planner.plan(request, agent, self.registry.definitions())
            if not steps:
                raise ValueError("Agent plan has no workflow steps")

            emit(AgentStatus.EXECUTING, "Executing workflow")
            for step in steps:
                if not self.registry.has(step.tool):
                    if step.required:
                        raise RuntimeError(f"Step '{step.id}' failed: Unknown tool: {step.tool}")
                    continue
                policy = step.retry_policy
                result = None
                for attempt in range(1, policy.max_attempts + 1):
                    emit(AgentStatus.EXECUTING, f"Executing step {step.id}", step.id, attempt)
                    inputs = {**run.context, **self._resolve(step.input, run.context)}
                    result = self._execute_with_timeout(step.tool, inputs, step.timeout_seconds)
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
                validation_errors.extend(validator(run).errors)
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
