# FundOps Agent Studio — Local Docker Setup & Verification

This guide documents the standard local Docker workflow for running and verifying the FundOps Agent Studio backend on a developer machine.

## 1. Prerequisites

Install and verify:

- Git
- Docker Desktop with Docker Compose support
- Access to the `Sunilkumarsahu11/fundops-agent-studio` GitHub repository
- A configured `.env` / environment configuration containing the required application settings and LLM credentials when LLM features are enabled

Check Docker:

```powershell
docker --version
docker compose version
```

Check Git:

```powershell
git --version
```

## 2. Clone the repository

If the project is not already present locally:

```powershell
git clone https://github.com/Sunilkumarsahu11/fundops-agent-studio.git
cd fundops-agent-studio
```

If it is already cloned, make sure the local checkout is current:

```powershell
cd E:\hackathon\fundops-agent-studio
git checkout main
git pull origin main
```

## 3. Configure environment variables

Before starting the backend, configure the environment variables expected by the application.

For LLM functionality, the important settings include:

```text
LLM_API_KEY=<your-api-key>
LLM_MODEL=<configured-model>
LLM_REASONING_EFFORT=none
LLM_MAX_PLAN_STEPS=10
LLM_MAX_PLAN_TOOLS=6
LLM_MAX_INPUT_CHARS=12000
LLM_MAX_OUTPUT_TOKENS=1200
LLM_MAX_RESULT_CHARS=12000
```

Do **not** commit API keys or other secrets to Git.

`LLM_MAX_PLAN_STEPS` is intentionally bounded. The current default is **10**, rather than unlimited, so the LLM cannot create arbitrarily large workflows.

## 4. Start the local Docker environment

For a clean rebuild of the backend:

```powershell
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

For normal development, when a clean rebuild is not required:

```powershell
docker compose up -d
```

## 5. Verify containers

Run:

```powershell
docker compose ps
```

The backend should show a healthy/running state and expose port `8000` when using the standard project configuration.

Example:

```text
NAME                              SERVICE    STATUS                   PORTS
fundops-agent-studio-backend-1    backend    Up ... (healthy)          0.0.0.0:8000->8000/tcp
```

If the database or other services are defined in the Compose file, verify those services are running as well.

## 6. Verify backend logs

Follow backend logs:

```powershell
docker compose logs -f backend
```

Look for successful application startup and absence of migration, import, configuration, or connection errors.

To inspect recent logs without following:

```powershell
docker compose logs --tail=200 backend
```

## 7. Verify the container contains the latest source

This is particularly important after changing Python source on GitHub and rebuilding Docker images.

Verify the OpenAI Responses API configuration:

```powershell
docker compose exec backend grep -n "use_responses_api" /workspace/app/agent_factory/llm.py
```

Expected:

```text
use_responses_api=True
```

Verify structured-output configuration:

```powershell
docker compose exec backend grep -n "strict=False" /workspace/app/agent_factory/llm.py
```

Expected:

```text
strict=False
```

Verify the workflow-step guardrail:

```powershell
docker compose exec backend grep -n "LLM_MAX_PLAN_STEPS" /workspace/app/agent_factory/llm.py
```

Expected source:

```python
self.max_steps = int(os.getenv("LLM_MAX_PLAN_STEPS", "10"))
```

These checks help detect a stale Docker image or an old source tree being mounted into the container.

## 8. Verify API health

If the application exposes a health endpoint, call the project's configured health URL. With the standard backend port:

```powershell
curl http://localhost:8000/health
```

If `/health` is not available in the current application version, inspect the API routes or use the application's documented endpoint instead.

You can also check that port 8000 is reachable:

```powershell
Test-NetConnection localhost -Port 8000
```

## 9. Verify LLM planner configuration

The planner currently uses LangChain's OpenAI integration with the OpenAI **Responses API**.

The important runtime settings are:

```text
API: Responses API
Structured planning: function calling
Reasoning configuration: Responses API reasoning={"effort": ...}
Default reasoning effort: none
Maximum workflow steps: 10
Maximum selected tools: 6
```

The architecture intentionally keeps the LLM advisory. Registered tools, deterministic validation, financial controls, and human approval remain authoritative.

## 10. Test `/agent-factory/draft-llm`

After the backend is healthy, send a request to the LLM planning endpoint using the project's current API contract.

For example, if the endpoint accepts JSON at:

```text
POST http://localhost:8000/agent-factory/draft-llm
```

use the request body expected by the current FastAPI schema.

A successful request should return a declarative agent blueprint rather than an OpenAI schema error or a workflow-step guardrail error.

### Expected failure modes

#### OpenAI structured schema error

If you see an error similar to:

```text
Invalid schema for response_format ... additionalProperties ... false
```

verify that the container has the current `LLMPlan` implementation and `strict=False` configuration.

#### Chat Completions / reasoning incompatibility

If you see:

```text
Function tools with reasoning_effort are not supported ... in /v1/chat/completions
```

verify that the container contains:

```python
use_responses_api=True
output_version="responses/v1"
reasoning={"effort": self.reasoning_effort}
```

Then rebuild the backend with `--no-cache`.

#### Workflow exceeds maximum steps

If you see:

```text
LLM plan exceeds maximum workflow steps: 10
```

this is a deterministic guardrail, not an LLM/API failure. The generated plan contains more than the configured maximum. Reduce the requested workflow complexity or explicitly raise `LLM_MAX_PLAN_STEPS` only when there is a justified operational need.

Do not remove the guardrail or set it to unlimited.

## 11. Troubleshooting stale containers/images

If the source checks show old code:

```powershell
git pull origin main
docker compose down
docker compose build --no-cache backend
docker compose up -d
docker compose ps
```

Then repeat the verification commands from Section 7.

To inspect images:

```powershell
docker compose images
```

To inspect the backend container:

```powershell
docker compose exec backend sh
```

Exit the shell with:

```sh
exit
```

## 12. Stop the environment

Stop containers while keeping volumes:

```powershell
docker compose down
```

If you need to remove Compose-managed volumes as part of a deliberate local reset:

```powershell
docker compose down -v
```

**Warning:** removing volumes can delete local database state. Use `-v` only when you intentionally want a clean local environment.

## 13. Recommended clean rebuild procedure

Use this procedure after significant backend or dependency changes:

```powershell
cd E:\hackathon\fundops-agent-studio
git checkout main
git pull origin main

docker compose down
docker compose build --no-cache backend
docker compose up -d
docker compose ps
docker compose logs --tail=200 backend
```

Then verify:

```powershell
docker compose exec backend grep -n "use_responses_api" /workspace/app/agent_factory/llm.py
docker compose exec backend grep -n "strict=False" /workspace/app/agent_factory/llm.py
docker compose exec backend grep -n "LLM_MAX_PLAN_STEPS" /workspace/app/agent_factory/llm.py
```

Finally, test the relevant API endpoint.

## 14. Quick verification checklist

- [ ] `docker --version` works
- [ ] `docker compose version` works
- [ ] Repository is on `main`
- [ ] `git pull origin main` completed successfully
- [ ] Required environment variables are configured
- [ ] No secrets are committed to Git
- [ ] `docker compose build --no-cache backend` succeeds when a clean rebuild is required
- [ ] `docker compose up -d` succeeds
- [ ] `docker compose ps` shows the backend as healthy/running
- [ ] Backend logs show successful startup
- [ ] `use_responses_api=True` is present in the running container
- [ ] `strict=False` is present in the running container
- [ ] `LLM_MAX_PLAN_STEPS` defaults to `10`
- [ ] Port `8000` is reachable
- [ ] `/agent-factory/draft-llm` can be exercised using the current API contract
- [ ] Deterministic workflow and financial guardrails remain enabled

## 15. Current LLM planner safety boundaries

The local deployment should retain these controls:

| Control | Current default | Purpose |
|---|---:|---|
| Maximum input characters | 12,000 | Bound prompt/input size |
| Maximum output tokens | 1,200 | Bound LLM output |
| Maximum workflow steps | 10 | Prevent oversized plans |
| Maximum selected tools | 6 | Limit workflow/tool surface |
| Result characters | 12,000 | Bound explanation context |
| Reasoning effort | `none` | Cost/latency-conscious default |
| Tool governance | Allow-listed only | Prevent arbitrary tool execution |
| Publication | Human approval required | Governance control |

These values are environment-configurable where appropriate, but production deployments should preserve explicit finite limits.
