from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid4

from app.agent_runtime.container import registry
from app.agent_runtime.registry import ToolRegistry

from .models import AgentInput, AgentKind, AgentOutput, FundAgentSpec


class FundOperationsLibrary:
    """Catalog and safe execution facade for reusable FundOps agents.

    Domain agents compose the shared deterministic tool layer. They do not
    duplicate financial-control implementations.
    """

    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        self.registry = tool_registry or registry
        self._agents = {spec.id: spec for spec in self._catalog()}
        self._handlers: dict[str, Callable[[AgentInput], AgentOutput]] = {
            "fund-reconciliation": self._reconcile,
            "excel-quality": self._excel_quality,
            "capital-call-review": self._capital_call_review,
            "nav-review": self._nav_review,
            "valuation-review": self._valuation_review,
            "normalization": self._normalization,
            "portfolio-exposure": self._portfolio_exposure,
            "investor-reporting": self._investor_reporting,
            "exception-investigation": self._investigate,
            "fund-data-qa": self._qa,
        }

    @staticmethod
    def _catalog() -> list[FundAgentSpec]:
        """Return the declarative agent catalogue.

        FundAgentSpec is a Pydantic model, so all fields are passed by name.
        Keeping the catalogue declarative also makes it safe for the Agent
        Factory to inspect and select from the same allow-listed agents.
        """
        return [
            FundAgentSpec(
                id="fund-reconciliation",
                name="Fund Reconciliation Agent",
                kind=AgentKind.RECONCILIATION,
                description="Compare two canonical fund datasets and produce evidence-backed exceptions.",
                capabilities=["composite-key-match", "tolerance", "materiality", "evidence"],
            ),
            FundAgentSpec(
                id="excel-quality",
                name="Excel Quality Agent",
                kind=AgentKind.EXCEL_QUALITY,
                description="Identify source workbook quality risks before ingestion.",
                capabilities=["structure-check", "header-check", "type-risk"],
            ),
            FundAgentSpec(
                id="capital-call-review",
                name="Capital Call Review Agent",
                kind=AgentKind.CAPITAL_CALL,
                description="Review capital-call records for deterministic completeness and consistency.",
                capabilities=["required-field-check", "duplicate-check", "amount-check"],
            ),
            FundAgentSpec(
                id="nav-review",
                name="NAV Review Agent",
                kind=AgentKind.NAV_REVIEW,
                description="Review NAV records and surface deterministic data-quality and movement exceptions.",
                capabilities=["completeness", "negative-check", "variance-review"],
            ),
            FundAgentSpec(
                id="valuation-review",
                name="Valuation Review Agent",
                kind=AgentKind.VALUATION_REVIEW,
                description="Review valuation records for amount, currency, date and evidence controls.",
                capabilities=["currency-check", "date-check", "amount-check"],
            ),
            FundAgentSpec(
                id="normalization",
                name="Fund Data Normalization Agent",
                kind=AgentKind.NORMALIZATION,
                description="Normalize mapped source data into the canonical fund model.",
                capabilities=["type-normalization", "provenance"],
            ),
            FundAgentSpec(
                id="portfolio-exposure",
                name="Portfolio Exposure Agent",
                kind=AgentKind.PORTFOLIO_EXPOSURE,
                description="Prepare portfolio exposure views from canonical investment records.",
                capabilities=["aggregation", "grouping", "percentage"],
            ),
            FundAgentSpec(
                id="investor-reporting",
                name="Investor Reporting Agent",
                kind=AgentKind.INVESTOR_REPORTING,
                description="Prepare governed investor-reporting datasets from canonical records.",
                capabilities=["aggregation", "uncalled-commitment", "evidence"],
            ),
            FundAgentSpec(
                id="exception-investigation",
                name="Exception Investigation Agent",
                kind=AgentKind.EXCEPTION_INVESTIGATION,
                description="Prioritize and explain existing deterministic exceptions without changing their outcomes.",
                capabilities=["reason-code", "evidence"],
            ),
            FundAgentSpec(
                id="fund-data-qa",
                name="Fund Data Q&A Agent",
                kind=AgentKind.FUND_DATA_QA,
                description="Answer questions over supplied canonical fund records without fabricating missing data.",
                capabilities=["record-lookup", "evidence"],
            ),
        ]

    def list(self) -> list[FundAgentSpec]:
        return list(self._agents.values())

    def get(self, agent_id: str) -> FundAgentSpec | None:
        return self._agents.get(agent_id)

    def execute(self, agent_id: str, request: AgentInput) -> AgentOutput:
        handler = self._handlers.get(agent_id)
        if handler is None:
            return AgentOutput(agent_id=agent_id, status="not_implemented", warnings=["This library agent is catalogued but its domain workflow is not yet enabled."])
        return handler(request)

    def _tool(self, name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        result = self.registry.execute(name, inputs)
        if not result.success:
            raise ValueError(result.error or f"Tool failed: {name}")
        return result.output

    def _run_domain_tool(self, agent_id: str, tool_name: str, request: AgentInput) -> AgentOutput:
        try:
            result = self._tool(tool_name, {
                "records": [r.model_dump(mode="json") for r in request.records],
                **request.parameters,
            })
            return AgentOutput(agent_id=agent_id, status=result.get("status", "completed"), result=result)
        except (KeyError, TypeError, ValueError) as exc:
            return AgentOutput(agent_id=agent_id, status="invalid_input", warnings=[str(exc)])

    def _reconcile(self, request: AgentInput) -> AgentOutput:
        p = request.parameters
        try:
            reconciliation = self._tool("reconcile_records", {
                "left_records": p["left_records"], "right_records": p["right_records"],
                "key_fields": p["key_fields"], "amount_field": p.get("amount_field"),
                "date_field": p.get("date_field"), "currency_field": p.get("currency_field"),
                "amount_tolerance": p.get("amount_tolerance", 0.0),
                "amount_tolerance_percent": p.get("amount_tolerance_percent", 0.0),
                "date_tolerance_days": p.get("date_tolerance_days", 0),
                "materiality_threshold": p.get("materiality_threshold", 0.0),
            })
            report = self._tool("build_exception_report", {"reconciliation_result": reconciliation})
            run_id = str(uuid4())
            self._tool("create_run_snapshot", {"run_id": run_id, "agent_id": "fund-reconciliation", "request": {"parameters": p}, "output": report, "status": reconciliation["status"]})
            self._tool("capture_audit_event", {"run_id": run_id, "agent_id": "fund-reconciliation", "action": "run_completed" if reconciliation["status"] == "matched" else "step_executed", "message": "Fund reconciliation completed", "details": {"exception_count": report["exception_count"]}})
            return AgentOutput(agent_id="fund-reconciliation", run_id=UUID(run_id), status=reconciliation["status"], result={"reconciliation": reconciliation, "report": report})
        except (KeyError, TypeError, ValueError) as exc:
            return AgentOutput(agent_id="fund-reconciliation", status="invalid_input", warnings=[str(exc)])

    def _excel_quality(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("excel-quality", "excel_quality", request)

    def _capital_call_review(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("capital-call-review", "capital_call_review", request)

    def _nav_review(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("nav-review", "nav_review", request)

    def _valuation_review(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("valuation-review", "valuation_review", request)

    def _normalization(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("normalization", "normalization_review", request)

    def _portfolio_exposure(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("portfolio-exposure", "portfolio_exposure", request)

    def _investor_reporting(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("investor-reporting", "investor_reporting", request)

    def _investigate(self, request: AgentInput) -> AgentOutput:
        return self._run_domain_tool("exception-investigation", "exception_investigation", request)

    def _qa(self, request: AgentInput) -> AgentOutput:
        question = str(request.parameters.get("question", "")).strip()
        if not question:
            return AgentOutput(agent_id="fund-data-qa", status="invalid_input", warnings=["question is required"])
        result = self._tool("query_records", {"records": [r.model_dump(mode="json") for r in request.records], "filters": request.parameters.get("filters", {})})
        result["question"] = question
        return AgentOutput(agent_id="fund-data-qa", status="completed", result=result)
