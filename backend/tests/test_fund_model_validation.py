from app.fund_model.default_model import build_default_model
from app.fund_model.records import CanonicalRecord
from app.fund_model.validation import validate_record


def test_valid_record_passes():
    model = build_default_model()
    record = CanonicalRecord(
        model_id=model.id,
        model_version=model.version,
        entity="Fund",
        data={"fund_id": "F-1", "name": "Demo Fund", "currency": "GBP"},
    )
    assert validate_record(record, model) == []


def test_unknown_and_missing_fields_are_reported():
    model = build_default_model()
    record = CanonicalRecord(model_id=model.id, model_version=model.version, entity="Fund", data={"unexpected": 1})
    errors = validate_record(record, model)
    assert "Missing required field: fund_id" in errors
    assert "Missing required field: name" in errors
    assert "Unknown field: unexpected" in errors
