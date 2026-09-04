# Phase 10 — LLM Optimization, Evaluation & Guardrails

FundOps Agent Studio now has an optional LangChain LLM layer on top of the existing deterministic Agent Runtime.

## What the LLM does

- Understands natural-language fund-operations requests.
- Produces a structured declarative workflow.
- Selects only registered tools exposed in the prompt.
- Explains deterministic results in natural language.

## What the LLM does not do

- Financial arithmetic.
- Reconciliation matching.
- Materiality calculations.
- Direct database mutations.
- Tool execution outside the allow-list.
- Agent publication without the existing human approval flow.

## API

`GET /agent-factory/llm/status`

Returns whether an LLM provider is configured.

`POST /agent-factory/draft-llm`

Example request:

```json
{
  "request": "Compare administrator and fund manager NAVs, flag differences above 1%, and produce an evidence-backed exception workflow",
  "name": "NAV Control Agent",
  "inputs": {
    "left_records": "$administrator_records",
    "right_records": "$manager_records",
    "amount_tolerance_percent": 1.0
  }
}
```

`POST /agent-factory/explain`

Accepts the original request and deterministic result and returns a constrained explanation.

## Guardrails

1. Structured Pydantic output from the LangChain model.
2. Only tools present in the deterministic registry can be selected.
3. Unknown tools cause the plan to be rejected.
4. Existing AgentFactory validation runs after LLM planning.
5. Financial control steps cannot be optional.
6. Temperature is fixed at zero for reproducibility.
7. Request and output limits prevent unbounded LLM payloads.
8. The prompt treats user text as untrusted input to reduce prompt-injection risk.
9. The LLM is explicitly prohibited from doing financial calculations.
10. Publication remains behind human approval.

## Cost controls

Configure:

```text
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
```

Keep the model small for planning/explanation and reserve larger models for cases where evaluation demonstrates a measurable quality benefit. The deterministic tools remain the source of truth, so LLM calls do not need to be used for arithmetic or reconciliation.

## Configuration

Set in `.env` or the runtime environment:

```text
LLM_PROVIDER=openai
LLM_MODEL=<model-name>
LLM_API_KEY=<provider-key>
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
```

The application starts without an API key. LLM endpoints return HTTP 503 until the provider is configured; deterministic endpoints continue to work.

## Evaluation strategy

The deterministic test suite verifies that an LLM-generated plan is:

- executable only through registered tools;
- rejected when it contains an unknown tool;
- passed through deterministic Factory validation;
- marked with planner and guardrail metadata.

For production/hackathon evaluation, keep a small golden set of representative requests covering reconciliation, NAV, valuation, capital calls, portfolio exposure, investor reporting, Excel quality, normalization and exception investigation. Score tool-selection accuracy, required-step coverage, invalid-plan rejection and explanation faithfulness. Do not score an LLM by asking it to recompute financial values.
