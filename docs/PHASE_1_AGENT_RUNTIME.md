# Phase 1 — Agent Runtime

## Objective

Build the reusable execution engine underneath every FundOps agent. The runtime is deliberately deterministic at the execution boundary: agents can select registered tools, but cannot execute arbitrary generated code.

## Runtime lifecycle

```text
AgentRequest
    ↓
UNDERSTAND
    ↓
PLAN (Planner interface)
    ↓
EXECUTE registered tools
    ↓
RETRY transient failures
    ↓
VALIDATE
    ↓
EXPLAIN
    ↓
COMPLETED / FAILED
```

## Implemented components

- **AgentDefinition** — declarative agent metadata and workflow steps.
- **WorkflowStep** — allow-listed tool reference, inputs, required flag, timeout and retry policy.
- **ToolDefinition** — description, input/output JSON-schema placeholders, determinism, version and default retry/timeout metadata.
- **ToolRegistry** — controlled tool execution boundary; unknown tools fail explicitly.
- **Planner / StaticPlanner** — planner abstraction ready for an LLM-backed planner later.
- **AgentRuntime** — executes planner output, maintains context, retries failures, emits events and invokes validators.
- **InMemoryAgentStore** — persistence boundary for definitions and runs; PostgreSQL replaces this in Phase 2.
- **ExecutionEvent** — lifecycle/step/attempt history retained for each run.
- **ValidationResult** — structured validation hook contract.
- **FastAPI API** — agent creation/list/get, tool discovery, run execution, run lookup and event history.
- **Phase 1 demo agent** — declarative YAML definition plus a smoke-test script.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/tools` | Discover registered tools |
| GET | `/agents` | List agents |
| POST | `/agents` | Register an agent definition |
| GET | `/agents/{agent_id}` | Fetch an agent |
| POST | `/agents/{agent_id}/run` | Execute an agent |
| GET | `/runs/{run_id}` | Fetch a run |
| GET | `/runs/{run_id}/events` | Fetch execution history |

## Retry behaviour

Retries are configured per workflow step. `max_attempts=1` means no retry. For failures marked retryable, the runtime retries until the attempt limit and optionally applies linear backoff between attempts. Financial operations should keep retries idempotent; the runtime never assumes a business operation is safe to repeat merely because it failed.

## Planner boundary

The current `StaticPlanner` returns the agent's declared steps. A future `LLMPlanner` may interpret natural-language requests and select a workflow, but its output must remain a validated list of registered `WorkflowStep` objects. The LLM never receives an unrestricted code-execution capability.

## Persistence boundary

Phase 1 uses `InMemoryAgentStore` so API and runtime contracts can be tested without prematurely coupling the engine to PostgreSQL. Phase 2 will introduce durable models, provenance and migrations behind the same logical boundary.

## Testing

Coverage includes:

- successful workflow execution;
- unknown required tools;
- retry of transient tool failures;
- event history;
- tool discovery;
- API agent creation and execution.

Run from `backend/`:

```bash
pytest -q
python scripts/phase1_smoke.py
```

## Deliberate non-goals

- no arbitrary Python execution;
- no distributed worker queue;
- no Kafka;
- no LLM provider dependency yet;
- no PostgreSQL persistence yet;
- no financial calculations in the runtime itself.

Those concerns belong in later phases or deterministic domain tools.
