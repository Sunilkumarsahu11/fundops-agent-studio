# Phase 10 — LLM Optimization, Evaluation & Guardrails — COMPLETE

FundOps Agent Studio has an optional **LangChain + OpenAI LLM planning/explanation layer** on top of the deterministic Agent Runtime.

## Architecture

```text
Natural language request
        |
        v
LangChain structured-output planner
        |
        +--> prompt-injection / size guardrails
        |
        v
Pydantic LLMPlan
        |
        +--> registered-tool allow-list
        +--> plan size limits
        +--> deterministic AgentFactory validation
        |
        v
Human approval before publish
        |
        v
Existing Agent Runtime
        |
        v
Deterministic FundOps tools + evidence + audit
        |
        v
Optional LangChain grounded explanation
```

## What the LLM does

- Understands natural-language fund-operations requests.
- Produces a structured declarative workflow.
- Selects only registered tools.
- Uses runtime context references such as `$records` and `$left_records`.
- Explains deterministic results in natural language.

## What the LLM never does

- Financial arithmetic.
- Reconciliation matching.
- Materiality calculations.
- Direct database mutations.
- Arbitrary code/tool execution.
- Agent publication or approval.
- Fabrication of evidence or financial figures.

## Implemented APIs

```text
GET  /agent-factory/llm/status
GET  /agent-factory/llm/metrics
POST /agent-factory/draft-llm
POST /agent-factory/explain
```

## Guardrails

1. Pydantic structured output from LangChain.
2. Tool selections must exist in the shared deterministic `ToolRegistry`.
3. Unknown tools are rejected.
4. Existing `AgentFactory.validate()` runs after LLM planning.
5. Financial control steps cannot be optional.
6. Temperature is fixed at zero.
7. Input size is bounded by `LLM_MAX_INPUT_CHARS`.
8. Output size is bounded by `LLM_MAX_OUTPUT_TOKENS`.
9. Workflow steps and tool selections have hard maximums.
10. Large result payloads are compacted before explanation.
11. Common prompt-injection/governance-bypass patterns are rejected.
12. User text is explicitly treated as untrusted data in the planner prompt.
13. Publication remains behind the existing human approval flow.
14. LLM failures do not disable deterministic FundOps workflows.

## Cost controls

```env
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
LLM_MAX_PLAN_STEPS=6
LLM_MAX_PLAN_TOOLS=6
LLM_MAX_RESULT_CHARS=12000
```

Planning and explanation requests are cached in-process using SHA-256 keys containing the operation, model, request and payload. `/agent-factory/llm/metrics` reports call/cache counters without exposing prompts or secrets.

For a hackathon, use a small/cheap model that passes the golden evaluation set. Do not spend tokens on calculations that deterministic Python already performs exactly.

## Evaluation

`backend/app/agent_factory/evaluation.py` contains a golden routing set covering:

- reconciliation;
- capital calls;
- NAV review;
- valuation review;
- portfolio exposure;
- investor reporting;
- Excel quality;
- normalization;
- exception investigation.

`backend/tests/test_llm_phase10.py` covers prompt-injection rejection, plan-size limits, result compaction, missing configuration, allow-listed structured planning and rejection of unregistered tools.

The evaluation principle is **tool-selection and workflow quality**, not asking the LLM to recompute financial numbers.

## Configuration

```env
LLM_PROVIDER=openai
LLM_MODEL=<model-name>
LLM_API_KEY=<provider-key>
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
LLM_MAX_PLAN_STEPS=6
LLM_MAX_PLAN_TOOLS=6
LLM_MAX_RESULT_CHARS=12000
```

The application remains usable without an API key. `/agent-factory/draft` remains deterministic; `/agent-factory/draft-llm` returns HTTP 503 when the LLM is not configured.

## Production direction

The current cache is intentionally process-local for the hackathon. A production deployment should replace it with a bounded Redis cache, add provider/model routing based on measured evaluation quality, and persist token/cost telemetry in the observability layer. The core governance boundary should remain unchanged.
