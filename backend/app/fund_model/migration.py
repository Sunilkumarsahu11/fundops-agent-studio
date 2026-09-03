from __future__ import annotations

from typing import Any

from .diff import diff_models
from .schema import FundModelDefinition


def migration_plan(old: FundModelDefinition, new: FundModelDefinition) -> dict[str, Any]:
    """Return reviewable operations; no data is mutated automatically."""
    diff = diff_models(old, new)
    operations = []
    for change in diff["changes"]:
        kind = change["kind"]
        if kind == "field_added":
            operations.append({"action": "add_field", "entity": change["entity"], "field": change["field"], "requires_backfill": change["risk"] == "high"})
        elif kind == "field_removed":
            operations.append({"action": "deprecate_field", "entity": change["entity"], "field": change["field"], "requires_review": True})
        elif kind == "field_type_changed":
            operations.append({"action": "transform_field", "entity": change["entity"], "field": change["field"], "from": change["from"], "to": change["to"], "requires_review": True})
        elif kind == "field_required":
            operations.append({"action": "backfill_required_field", "entity": change["entity"], "field": change["field"], "requires_review": True})
        elif kind == "entity_removed":
            operations.append({"action": "retire_entity", "entity": change["entity"], "requires_review": True})
        else:
            operations.append({"action": "review", **change})
    return {"diff": diff, "operations": operations, "automatic_execution": False}
