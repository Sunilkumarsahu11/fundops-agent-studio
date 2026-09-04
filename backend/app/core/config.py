from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FundOps Agent Studio"
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://fundops:fundops@localhost:5432/fundops"
    llm_provider: str = "openai"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_max_input_chars: int = 12000
    llm_max_output_tokens: int = 1200
    llm_max_plan_steps: int = 6
    llm_max_plan_tools: int = 6
    llm_max_result_chars: int = 12000

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
