from app.agent_factory.factory import AgentFactory
from app.agent_factory.models import FactoryRequest
from app.agent_runtime.container import registry
from app.agent_runtime.models import AgentRequest
from app.agent_runtime.runtime import AgentRuntime


def test_factory_uses_shared_registry_and_generates_tool_chain():
    factory = AgentFactory(registry)
    blueprint = factory.draft(FactoryRequest(request="Reconcile two fund datasets and flag material exceptions"))
    assert [step.tool for step in blueprint.steps] == ["reconcile_records", "build_exception_report"]
    assert factory.validate(blueprint).valid
    assert blueprint.steps[1].input["reconciliation_result"] == "$step_1"


def test_runtime_resolves_context_references_between_tools():
    factory = AgentFactory(registry)
    blueprint = factory.draft(FactoryRequest(request="Reconcile two fund datasets and flag material exceptions"))
    agent = factory.publish(blueprint, "test-user")
    run = AgentRuntime(registry).run(agent, AgentRequest(request="run", inputs={
        "left_records": [], "right_records": [], "key_fields": ["id"],
        "amount_field": None, "date_field": None, "currency_field": None,
        "amount_tolerance": 0, "amount_tolerance_percent": 0,
        "date_tolerance_days": 0, "materiality_threshold": 0,
    }))
    assert run.status.value == "completed"
    assert "step_1" in run.context
    assert "step_2" in run.context
    assert run.context["step_2"]["exception_count"] == 0
