from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from .records import CanonicalRecord
from .schema import FieldType, FundModelDefinition


def validate_record(record: CanonicalRecord, model: FundModelDefinition) -> list[str]:
    errors: list[str] = []
    if record.model_id != model.id or record.model_version != model.version:
        return ["Record model id/version does not match the supplied schema"]
    entity = next((e for e in model.entities if e.name == record.entity), None)
    if entity is None:
        return [f"Unknown entity: {record.entity}"]
    fields = {field.name: field for field in entity.fields}
    for field in entity.fields:
        if field.required and field.name not in record.data:
            errors.append(f"Missing required field: {field.name}")
        if field.name in record.data and record.data[field.name] is None and not field.nullable:
            errors.append(f"Field cannot be null: {field.name}")
    for name in record.data:
        if name not in fields:
            errors.append(f"Unknown field: {name}")
            continue
        value = record.data[name]
        field = fields[name]
        if value is None:
            continue
        valid = {
            FieldType.STRING: isinstance(value, str),
            FieldType.INTEGER: isinstance(value, int) and not isinstance(value, bool),
            FieldType.NUMBER: isinstance(value, (int, float, Decimal)) and not isinstance(value, bool),
            FieldType.BOOLEAN: isinstance(value, bool),
            FieldType.DATE: isinstance(value, date) and not isinstance(value, datetime),
            FieldType.DATETIME: isinstance(value, datetime),
            FieldType.MONEY: isinstance(value, (int, float, Decimal)) and not isinstance(value, bool),
            FieldType.ENUM: value in field.enum_values,
            FieldType.REFERENCE: isinstance(value, str),
            FieldType.JSON: isinstance(value, dict),
        }[field.type]
        if not valid:
            errors.append(f"Invalid type/value for field: {name}")
    return errors
