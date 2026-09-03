from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.fund_model.schema import EntityDefinition, FieldDefinition, FundModelDefinition

from .models import MappingCandidate, MappingResult, SourceTable, UnmappedField


def suggest_mappings(tables: list[SourceTable], model: FundModelDefinition) -> MappingResult:
    fields = [(entity, field) for entity in model.entities for field in entity.fields]
    candidates: list[MappingCandidate] = []
    unmapped: list[UnmappedField] = []
    for table in tables:
        for column in table.columns:
            best: tuple[float, EntityDefinition | None, FieldDefinition | None] = (0, None, None)
            for entity, field in fields:
                score = _score(column.name, entity.name, field)
                if score > best[0]:
                    best = (score, entity, field)
            if best[1] is None or best[2] is None or best[0] < 0.55:
                unmapped.append(UnmappedField(source_field=column.name, reason="No sufficiently strong model-field match"))
                continue
            confidence = min(1.0, best[0])
            candidates.append(MappingCandidate(source_field=column.name, target_entity=best[1].name, target_field=best[2].name, confidence=confidence, reason="Name/label semantic similarity", requires_review=confidence < 0.80))
    return MappingResult(model_id=model.id, model_version=model.version, candidates=candidates, unmapped=unmapped)


def _score(source: str, entity_name: str, field: FieldDefinition) -> float:
    source_tokens = _tokens(source)
    field_tokens = _tokens(field.name + " " + field.label)
    exact = 1.0 if source_tokens == field_tokens else 0.0
    overlap = len(source_tokens & field_tokens) / max(1, len(source_tokens | field_tokens))
    similarity = SequenceMatcher(None, _normal(source), _normal(field.name)).ratio()
    entity_hint = 0.05 if _normal(entity_name) in _normal(source) else 0.0
    return max(exact, 0.65 * similarity + 0.35 * overlap) + entity_hint


def _normal(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9]+", value.lower()) if token}
