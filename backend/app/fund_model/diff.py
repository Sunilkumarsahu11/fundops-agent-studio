from __future__ import annotations

from typing import Any

from .schema import FundModelDefinition


def diff_models(old: FundModelDefinition, new: FundModelDefinition) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    old_entities = {e.name: e for e in old.entities}
    new_entities = {e.name: e for e in new.entities}
    for name in sorted(new_entities.keys() - old_entities.keys()):
        changes.append({"kind": "entity_added", "entity": name, "risk": "low"})
    for name in sorted(old_entities.keys() - new_entities.keys()):
        changes.append({"kind": "entity_removed", "entity": name, "risk": "high"})
    for name in sorted(old_entities.keys() & new_entities.keys()):
        of = {f.name: f for f in old_entities[name].fields}
        nf = {f.name: f for f in new_entities[name].fields}
        for field in sorted(nf.keys() - of.keys()):
            risk = "high" if nf[field].required else "low"
            changes.append({"kind": "field_added", "entity": name, "field": field, "risk": risk})
        for field in sorted(of.keys() - nf.keys()):
            changes.append({"kind": "field_removed", "entity": name, "field": field, "risk": "high"})
        for field in sorted(of.keys() & nf.keys()):
            if of[field].type != nf[field].type:
                changes.append({"kind": "field_type_changed", "entity": name, "field": field, "from": of[field].type, "to": nf[field].type, "risk": "high"})
            if not of[field].required and nf[field].required:
                changes.append({"kind": "field_required", "entity": name, "field": field, "risk": "high"})
            if of[field].enum_values != nf[field].enum_values:
                changes.append({"kind": "enum_changed", "entity": name, "field": field, "from": of[field].enum_values, "to": nf[field].enum_values, "risk": "medium"})
    return {
        "from": {"id": old.id, "version": old.version},
        "to": {"id": new.id, "version": new.version},
        "compatible": not any(c["risk"] == "high" for c in changes),
        "changes": changes,
    }
