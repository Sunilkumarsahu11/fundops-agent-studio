# Phase 1 — Agent Runtime

## Objective

Create the reusable execution engine underneath every FundOps agent.

## Runtime contract

```text
AgentRequest
    ↓
UNDERSTAND
    ↓
PLAN
    ↓
EXECUTE workflow steps
    ↓
VALIDATE
    ↓
EXPLAIN
    ↓
COMPLETED / FAILED
```

## Components

### AgentDefinition

Describes an agent and its ordered workflow steps.

### WorkflowStep

References a registered deterministic tool and optional static inputs.

### ToolRegistry

Provides the controlled execution boundary between agents and application capabilities. Unknown tools fail explicitly.

### AgentRuntime

Creates a run, maintains execution context, emits lifecycle events, executes steps, captures failures and returns structured output.

### AgentRun

Contains the run identifier, request, status, context, output and errors.

## Design rules

1. Agents execute declared tools; they do not execute arbitrary generated Python.
2. Tool failures are captured as structured runtime failures.
3. Required workflow steps fail the run when unsuccessful.
4. Optional steps can fail without aborting the entire workflow.
5. Runtime state is structured so persistence can be introduced in a later phase.
6. LLM planning will be added above the runtime; deterministic tools remain below it.

## Current implementation

Phase 1 starts with a synchronous in-process runtime. This is deliberate. Persistence, asynchronous execution, retries, distributed workers and streaming can be added once the workflow contract is stable.

## Next extensions

- planner interface;
- persistent run store;
- retry policy and backoff;
- timeout/cancellation;
- tool metadata and JSON schemas;
- validation hooks;
- event persistence;
- LLM-backed plan generation;
- human approval checkpoints.
