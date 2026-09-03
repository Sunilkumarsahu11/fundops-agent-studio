from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.fund_model.record import CanonicalRecord


class AgentKind(str, Enum):
    RECONCILIATION = "reconciliation"
    EXCEL_QUALITY = "excel_quality"
    CAPITAL_CALL = "capital_call"
    NAV_REVIEW = "nav_review"
    VALUATION_REVIEW = "valuation_review"
    NORMALIZATION = "normalization"
    PORTFOLIO_EXPOSURE = "portfolio_exposure"
    INVESTOR_REPORTING = "investor_reporting"
    EXCEPTION_INVESTIGATION = "exception_investigation"
    FUND_DATA_QA = "fund_data_qa"


class FundAgentSpec(BaseModel):
    id: str
    name: str
    kind: AgentKind
    description: str
    deterministic: bool = True
    version: str = "1.0.0"
    capabilities: list[str] = Field(default_factory=list)


class AgentInput(BaseModel):
    records: list[CanonicalRecord] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_id: str
    run_id: UUID = Field(default_factory=uuid4)
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
