from app.agent_runtime.container import registry
from app.fund_model.records import CanonicalRecord, Provenance
from app.fund_ops.library import FundOperationsLibrary
from app.fund_ops.models import AgentInput


def record(entity: str, data: dict, source: str) -> CanonicalRecord:
    return CanonicalRecord(
        model_id="starter-fund-model",
        model_version=1,
        entity=entity,
        data=data,
        provenance=[Provenance(source_file=source, source_sheet="Data", source_cell="A1")],
    )


def test_domain_tools_are_registered():
    assert {"capital_call_review", "nav_review", "valuation_review", "portfolio_exposure", "investor_reporting"}.issubset(set(registry.names()))


def test_capital_call_review_detects_duplicate_missing_and_invalid_amount():
    calls = [
        record("CapitalCall", {"fund_id": "F1", "call_id": "CC1", "amount": 100}, "admin.xlsx"),
        record("CapitalCall", {"fund_id": "F1", "call_id": "CC1", "amount": -25}, "admin.xlsx"),
        record("CapitalCall", {"fund_id": "F1", "amount": 50}, "admin.xlsx"),
    ]
    result = registry.execute("capital_call_review", {"records": [r.model_dump(mode="json") for r in calls]})
    assert result.success
    assert result.output["exception_count"] == 3
    assert result.output["total_call_amount"] == 125


def test_nav_review_detects_negative_and_threshold_movement():
    records = [
        record("NAV", {"fund_id": "F1", "nav": 110, "prior_nav": 100}, "nav.xlsx"),
        record("NAV", {"fund_id": "F2", "nav": -5, "prior_nav": 0}, "nav.xlsx"),
    ]
    result = registry.execute("nav_review", {"records": [r.model_dump(mode="json") for r in records], "variance_percent_threshold": 5})
    assert result.success
    assert result.output["exception_count"] == 2
    assert result.output["nav_by_fund"]["F1"] == 110


def test_valuation_review_checks_amount_currency_and_date():
    records = [record("Valuation", {"fair_value": -10, "currency": "XYZ"}, "valuation.xlsx")]
    result = registry.execute("valuation_review", {"records": [r.model_dump(mode="json") for r in records], "allowed_currencies": ["GBP", "USD"]})
    assert result.success
    assert {e["code"] for e in result.output["exceptions"]} == {"NEGATIVE_VALUATION", "UNSUPPORTED_CURRENCY", "MISSING_VALUATION_DATE"}


def test_portfolio_exposure_aggregates_and_percentages():
    records = [
        record("Investment", {"sector": "Tech", "fair_value": 300, "currency": "GBP"}, "portfolio.xlsx"),
        record("Investment", {"sector": "Tech", "fair_value": 100, "currency": "GBP"}, "portfolio.xlsx"),
        record("Investment", {"sector": "Healthcare", "fair_value": 100, "currency": "GBP"}, "portfolio.xlsx"),
    ]
    result = registry.execute("portfolio_exposure", {"records": [r.model_dump(mode="json") for r in records]})
    assert result.success
    assert result.output["total_exposure"] == 500
    assert result.output["exposure"][0] == {"group": "Tech", "amount": 400, "percentage": 80.0}


def test_investor_reporting_builds_governed_totals():
    records = [
        record("Commitment", {"investor_id": "I1", "commitment": 1000, "capital_called": 250}, "investors.xlsx"),
        record("Investor", {"investor_id": "I1", "distribution": 50, "nav": 900}, "investors.xlsx"),
        record("Commitment", {"investor_id": "I2", "commitment": 500, "capital_called": 100}, "investors.xlsx"),
    ]
    result = registry.execute("investor_reporting", {"records": [r.model_dump(mode="json") for r in records]})
    assert result.success
    rows = {row["investor"]: row for row in result.output["rows"]}
    assert rows["I1"]["commitment"] == 1000
    assert rows["I1"]["capital_called"] == 250
    assert rows["I1"]["uncalled_commitment"] == 750
    assert rows["I1"]["evidence_count"] == 2


def test_library_catalog_agents_are_executable():
    library = FundOperationsLibrary(registry)
    assert library.execute("capital-call-review", AgentInput(records=[], parameters={})).status == "passed"
    assert library.execute("nav-review", AgentInput(records=[], parameters={})).status == "passed"
    assert library.execute("valuation-review", AgentInput(records=[], parameters={})).status == "passed"
    assert library.execute("portfolio-exposure", AgentInput(records=[], parameters={})).status == "completed"
    assert library.execute("investor-reporting", AgentInput(records=[], parameters={})).status == "completed"
