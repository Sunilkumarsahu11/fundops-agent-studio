from fastapi import FastAPI

app = FastAPI(
    title="FundOps Agent Studio",
    version="0.1.0",
    description="Configurable AI agents for private-market fund operations.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fundops-agent-studio"}
