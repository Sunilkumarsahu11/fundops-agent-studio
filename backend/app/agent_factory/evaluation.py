from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent_runtime.registry import ToolRegistry


@dataclass(frozen=True)
class EvaluationCase:
    request: str
    expected_tool: str


DEFAULT_CASES = (
    EvaluationCase("reconcile administrator and manager NAV", "reconcile_records"),
    EvaluationCase("review capital calls for invalid amounts", "capital_call_review"),
    EvaluationCase("perform a NAV review", "nav_review"),
    EvaluationCase("review portfolio valuation currency", "valuation_review"),
    EvaluationCase("analyse portfolio exposure by sector", "portfolio_exposure"),
    EvaluationCase("prepare investor reporting", "investor_reporting"),
    EvaluationCase("check Excel workbook quality", "excel_quality"),
    EvaluationCase("normalize canonical records", "normalization_review"),
    EvaluationCase("triage exception records", "exception_investigation"),
)


class LLMPlanEvaluator:
    """Small deterministic regression suite for the LLM planner contract."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def evaluate(self, planner: Any, cases: tuple[EvaluationCase, ...] = DEFAULT_CASES) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for case in cases:
            try:
                blueprint = planner.plan(type("Request", (), {"request": case.request, "name": None, "inputs": {}})())
                tools = [step.tool for step in blueprint.steps]
                passed = case.expected_tool in tools
                results.append({"request": case.request, "expected_tool": case.expected_tool, "actual_tools": tools, "passed": passed})
            except Exception as exc:
                results.append({"request": case.request, "expected_tool": case.expected_tool, "actual_tools": [], "passed": False, "error": str(exc)})
        passed = sum(1 for item in results if item["passed"])
        return {"case_count": len(results), "passed": passed, "failed": len(results) - passed, "accuracy": passed / len(results) if results else 1.0, "results": results}
