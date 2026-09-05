import pytest

from app.agent_runtime.builtins import register_builtins
from app.agent_runtime.registry import ToolRegistry


def test_builtin_tool_layer_is_registered():
    registry = ToolRegistry()
    register_builtins(registry)
    assert {
        "inspect_source",
        "ingest_source",
        "map_source_to_model",
        "normalize_records",
        "validate_records",
        "query_records",
        "get_record_evidence",
        "reconcile_records",
        "calculate_variance",
        "evaluate_materiality",
        "build_exception_report",
        "capital_call_review",
        "nav_review",
        "valuation_review",
        "portfolio_exposure",
        "investor_reporting",
        "excel_quality",
        "normalization_review",
        "exception_investigation",
        "collect_evidence",
        "create_run_snapshot",
        "capture_audit_event",
        "request_approval",
        "approve",
        "reject",
    }.issubset(set(registry.names()))


def test_variance_tool_is_deterministic():
    registry = ToolRegistry()
    register_builtins(registry)
    result = registry.execute("calculate_variance", {"left": 1200, "right": 1000})
    assert result.success
    assert result.output["variance"] == 200
    assert result.output["absolute_variance"] == 200
    assert result.output["variance_percent"] == pytest.approx(200 / 12)


def test_materiality_tool_is_deterministic():
    registry = ToolRegistry()
    register_builtins(registry)
    result = registry.execute("evaluate_materiality", {"variance": 101, "threshold": 100})
    assert result.success
    assert result.output["material"] is True
