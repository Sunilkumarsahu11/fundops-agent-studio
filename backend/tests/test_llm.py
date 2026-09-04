from app.agent_factory.llm import LLMPlan, LLMPlanner, LLMToolSelection, LLMWorkflowStep, LLMUnavailableError
from app.agent_factory.models import FactoryRequest
from app.agent_runtime.container import registry


def test_llm_planner_requires_configuration_without_calling_provider() -> None:
    planner = LLMPlanner(registry, model="", api_key="")
    assert planner.configured is False
    try:
        planner.plan(FactoryRequest(request="reconcile administrator and manager NAV"))
    except LLMUnavailableError:
        pass
    else:
        raise AssertionError("Expected LLMUnavailableError")


def test_llm_plan_is_converted_and_deterministically_validated() -> None:
    planner = LLMPlanner(registry, model="test-model", api_key="test-key")
    plan = LLMPlan(
        name="NAV reconciliation",
        description="Compare two independent NAV datasets and report material exceptions.",
        tools=[
            LLMToolSelection(tool="reconcile_records", reason="Compare administrator and manager records.", confidence=0.96),
            LLMToolSelection(tool="build_exception_report", reason="Produce an exception report.", confidence=0.94),
        ],
        steps=[
            LLMWorkflowStep(tool="reconcile_records", input={"left_records": "$left_records", "right_records": "$right_records", "key_fields": "$key_fields", "amount_field": "$amount_field"}),
            LLMWorkflowStep(tool="build_exception_report", input={"reconciliation_result": "$step_1"}),
        ],
    )
    blueprint = planner._to_blueprint(FactoryRequest(request="reconcile administrator and manager NAV"), plan)
    assert blueprint.metadata["planner"] == "langchain-llm"
    assert [step.tool for step in blueprint.steps] == ["reconcile_records", "build_exception_report"]
    assert blueprint.metadata["llm_guardrails"]


def test_llm_plan_rejects_unknown_tools() -> None:
    planner = LLMPlanner(registry, model="test-model", api_key="test-key")
    plan = LLMPlan(
        name="Unsafe",
        description="Should fail",
        tools=[LLMToolSelection(tool="delete_all_funds", reason="not registered", confidence=1.0)],
        steps=[LLMWorkflowStep(tool="delete_all_funds")],
    )
    try:
        planner._to_blueprint(FactoryRequest(request="do something"), plan)
    except ValueError as exc:
        assert "unregistered tools" in str(exc)
    else:
        raise AssertionError("Expected unknown tool rejection")
