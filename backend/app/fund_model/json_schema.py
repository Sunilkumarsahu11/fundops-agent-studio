from typing import Any

from .schema import FieldType, FundModelDefinition


def field_to_json_schema(field) -> dict[str, Any]:
    mapping = {
        FieldType.STRING: {"type": "string"},
        FieldType.INTEGER: {"type": "integer"},
        FieldType.NUMBER: {"type": "number"},
        FieldType.BOOLEAN: {"type": "boolean"},
        FieldType.DATE: {"type": "string", "format": "date"},
        FieldType.DATETIME: {"type": "string", "format": "date-time"},
        FieldType.MONEY: {"type": "number"},
        FieldType.ENUM: {"type": "string", "enum": field.enum_values},
        FieldType.REFERENCE: {"type": "string", "x-reference-entity": field.reference_entity},
        FieldType.JSON: {"type": "object"},
    }
    result = dict(mapping[field.type])
    result.update(field.validation)
    if field.description:
        result["description"] = field.description
    if field.nullable:
        result = {"anyOf": [result, {"type": "null"}]}
    return result


def model_to_json_schema(model: FundModelDefinition) -> dict[str, Any]:
    entities = {}
    for entity in model.entities:
        required = [f.name for f in entity.fields if f.required]
        properties = {f.name: field_to_json_schema(f) for f in entity.fields}
        entities[entity.name] = {
            "type": "object",
            "title": entity.label,
            "description": entity.description,
            "properties": properties,
            "required": required,
            "additionalProperties": False,
            "x-version": entity.version,
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": model.name,
        "type": "object",
        "properties": {"entity": {"enum": list(entities)} , "data": {"oneOf": list(entities.values())}},
        "x-model-id": model.id,
        "x-model-version": model.version,
        "x-entities": entities,
    }
