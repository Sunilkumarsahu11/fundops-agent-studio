from collections.abc import Callable
from typing import Any
from uuid import UUID, uuid4

from app.agent_runtime.container import registry
from app.agent_runtime.registry import ToolRegistry
from app.reconciliation.agent import FundReconciliationAgent

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
            "exception-investigation": self._investigate,
            "fund-data-qa": self._qa,
        }

    @staticmethod
    def _catalog() -> list[FundAgentSpec]:
        return [
            FundAgentSpec("fund-reconciliation", "Fund Reconciliation Agent", AgentKind.RECONCILIATION, "Compare two canonical fund datasets and produce evidence-backed exceptions.", capabilities=["composite-key-match", "tolerance", "materiality", "evidence"]),
            FundAgentSpec("excel-quality", "Excel Quality Agent", AgentKind.EXCEL_QUALITY, "Identify source workbook quality risks before ingestion.", capabilities=["structure-check", "header-check", "type-risk"]),
            FundAgentSpec("capital-call-review", "Capital Call Review Agent", AgentKind.CAPITAL_CALL, "Review capital-call records for deterministic completeness and consistency.", capabilities=["required-field-check", "amount-check"]),
            FundAgentSpec("nav-review", "NAV Review Agent", AgentKind.NAV_REVIEW, "Review NAV records and surface data-quality exceptions.", capabilities=["completeness", "variance-review"]),
            FundAgentSpec("valuation-review", "Valuation Review Agent", AgentKind.VALUATION_REVIEW, "Review valuation records for consistency and evidence coverage.", capabilities=["currency-check", "date-check", "variance-review"]),
            FundAgentSpec("normalization", "Fund Data Normalization Agent", AgentKind.NORMALIZATION, "Normalize mapped source data into the canonical fund model.", capabilities=["type-normalization", "provenance"]),
            FundAgentSpec("portfolio-exposure", "Portfolio Exposure Agent", AgentKind.PORTFOLIO_EXPOSURE, "Prepare portfolio exposure views from canonical investment records.", capabilities=["aggregation", "grouping"]),
            FundAgentSpec("investor-reporting", "Investor Reporting Agent", AgentKind.INVESTOR_REPORTING, "Prepare governed investor-reporting datasets from canonical records.", capabilities=["aggregation", "evidence"]),
            FundAgentSpec("exception-investigation", "Exception Investigation Agent", AgentKind.EXCEPTION_INVESTIGATION, "Prioritize and explain existing deterministic exceptions without changing their outcomes.", capabilities=["reason-code", "evidence"]),
            FundAgentSpec("fund-data-qa", "Fund Data Q&A Agent", AgentKind.FUND_DATA_QA, "Answer questions over supplied canonical fund records without fabricating missing data.", capabilities=["record-lookup", "evidence"]),
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

    def _reconcile(self, request: AgentInput) -> AgentOutput:
        p = request.parameters
        try:
            left = p["left_records"]
            right = p["right_records"]
            reconciliation = self._tool("reconcile_records", {
                "left_records": left,
                "right_records": right,
                "key_fields": p["key_fields"],
                "amount_field": p.get("amount_field"),
                "date_field": p.get("date_field"),
                "currency_field": p.get("currency_field"),
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

    def _investigate(self, request: AgentInput) -> AgentOutput:
        exceptions = request.parameters.get("exceptions", [])
        evidence = [item.get("evidence", {}) for item in exceptions if isinstance(item, dict)]
        return AgentOutput(agent_id="exception-investigation", status="completed", result={"exception_count": len(exceptions), "exceptions": exceptions, "evidence": evidence})

    def _qa(self, request: AgentInput) -> AgentOutput:
        question = str(request.parameters.get("question", "")).strip()
        if not question:
            return AgentOutput(agent_id="fund-data-qa", status="invalid_input", warnings=["question is required"])
        result = self._tool("query_records", {"records": [r.model_dump(mode="json") for r in request.records], "filters": request.parameters.get("filters", {})})
        result["question"] = question
        return AgentOutput(agent_id="fund-data-qa", status="completed", result=result)
