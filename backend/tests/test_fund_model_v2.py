from app.fund_model.default_model import build_default_model
from app.fund_model.diff import diff_models
from app.fund_model.json_schema import model_to_json_schema
from app.fund_model.overlay import apply_overlay
from app.fund_model.schema import EntityDefinition, FieldDefinition, FieldType, FundModelDefinition


def test_json_schema_contains_entities_and_required_fields():
    model = build_default_model()
    schema = model_to_json_schema(model)
    assert schema["x-model-version"] == model.version
    assert "Fund" in schema["x-entities"]
    assert "fund_id" in schema["x-entities"]["Fund"]["required"]


def test_diff_detects_breaking_change():
    old = build_default_model()
    new = old.model_copy(deep=True)
    new.version = 2
    fund = next(entity for entity in new.entities if entity.name == "Fund")
    currency = next(field for field in fund.fields if field.name == "currency")
    currency.required = True
    currency.nullable = False
    result = diff_models(old, new)
    assert result["compatible"] is False
    assert any(item["kind"] == "field_required" for item in result["changes"])


def test_overlay_adds_client_specific_field():
    base = build_default_model()
    overlay = FundModelDefinition(
        id="client-a-model",
        name="Client A Fund Model",
        version=1,
        entities=[
            EntityDefinition(
                name="Fund",
                label="Fund",
                fields=[
                    FieldDefinition(
                        name="risk_rating",
                        label="Risk Rating",
                        type=FieldType.ENUM,
                        enum_values=["low", "medium", "high"],
                    )
                ],
            )
        ],
    )
    result = apply_overlay(base, overlay)
    fund = next(entity for entity in result.entities if entity.name == "Fund")
    assert "fund_id" in {field.name for field in fund.fields}
    assert "risk_rating" in {field.name for field in fund.fields}
    assert result.metadata["base_model"]["id"] == base.id
