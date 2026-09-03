import pytest

from app.fund_model.default_model import default_fund_model
from app.fund_model.registry import FundModelRegistry
from app.fund_model.schema import FieldDefinition, FieldType, FundModelDefinition


def test_default_model_is_configuration_driven() -> None:
    model = default_fund_model()
    assert model.id == "private-markets-core"
    assert {entity.name for entity in model.entities} >= {"Fund", "Investor", "Commitment", "Investment", "Valuation", "CapitalCall"}


def test_registry_supports_multiple_versions() -> None:
    registry = FundModelRegistry()
    v1 = default_fund_model()
    v2 = v1.model_copy(deep=True, update={"version": 2})
    registry.register(v1)
    registry.register(v2)

    assert registry.get(v1.id).version == 2
    assert registry.get(v1.id, 1).version == 1


def test_registry_rejects_duplicate_version() -> None:
    registry = FundModelRegistry()
    model = default_fund_model()
    registry.register(model)
    with pytest.raises(ValueError, match="already exists"):
        registry.register(model)


def test_enum_requires_values() -> None:
    with pytest.raises(ValueError, match="enum_values"):
        FieldDefinition(name="status", label="Status", type=FieldType.ENUM)


def test_model_can_be_extended_without_code_changes() -> None:
    model = FundModelDefinition(
        id="client-model",
        name="Client Model",
        entities=[
            {
                "name": "Investor",
                "label": "Investor",
                "fields": [
                    {"name": "investor_id", "label": "Investor ID", "type": "string", "required": True, "nullable": False},
                    {"name": "investor_type", "label": "Investor Type", "type": "enum", "enum_values": ["institutional", "family_office"]},
                ],
            }
        ],
    )
    assert model.entities[0].fields[1].enum_values == ["institutional", "family_office"]
