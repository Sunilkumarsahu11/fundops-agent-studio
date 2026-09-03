from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Configurable AI agents for private-market fund operations.",
)

app.include_router(router)
