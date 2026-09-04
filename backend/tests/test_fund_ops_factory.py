import pytest

from app.agent_factory.factory import AgentFactory
from app.agent_factory.models import FactoryRequest
from app.agent_runtime.container import registry


@pytest.mark.parametrize(
    ("request", "tool"),
    [
        ("Review capital calls for missing fields and invalid amounts", "capital_call_review"),
        ("Perform a NAV review and flag large movements", "nav_review"),
        ("Run valuation review for currency and date issues", "valuation_review"),
        ("Analyse portfolio exposure by sector", "portfolio_exposure"),
        ("Prepare investor reporting by investor", "investor_reporting"),
    ],
)
def test_factory_generates_registered_domain_tool(request: str, tool: str):
    factory = AgentFactory(registry)
    blueprint = factory.draft(FactoryRequest(request=request))
    assert [step.tool for step in blueprint.steps] == [tool]
    assert factory.validate(blueprint).valid
