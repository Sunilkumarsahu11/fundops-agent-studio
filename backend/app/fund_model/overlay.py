from copy import deepcopy

from .schema import EntityDefinition, FieldDefinition, FundModelDefinition


def apply_overlay(base: FundModelDefinition, overlay: FundModelDefinition) -> FundModelDefinition:
    """Create a tenant/client model by applying an additive/override overlay to a base version."""
    result = deepcopy(base)
    entities = {entity.name: entity for entity in result.entities}
    for incoming in overlay.entities:
        if incoming.name not in entities:
            entities[incoming.name] = deepcopy(incoming)
            continue
        target = entities[incoming.name]
        fields = {field.name: field for field in target.fields}
        for field in incoming.fields:
            fields[field.name] = deepcopy(field)
        target.fields = list(fields.values())
        relationships = {relationship.name: relationship for relationship in target.relationships}
        for relationship in incoming.relationships:
            relationships[relationship.name] = deepcopy(relationship)
        target.relationships = list(relationships.values())
        target.metadata.update(incoming.metadata)
    result.entities = list(entities.values())
    result.metadata.update(overlay.metadata)
    result.metadata["base_model"] = {"id": base.id, "version": base.version}
    result.id = overlay.id
    result.name = overlay.name
    result.version = overlay.version
    result.status = overlay.status
    return FundModelDefinition.model_validate(result)
