from .schema import EntityDefinition, FundModelDefinition


class FundModelRegistry:
    """In-memory schema registry; PostgreSQL persistence will be added in Phase 2."""

    def __init__(self) -> None:
        self._models: dict[tuple[str, int], FundModelDefinition] = {}

    def register(self, model: FundModelDefinition) -> None:
        key = (model.id, model.version)
        if key in self._models:
            raise ValueError(f"Fund model version already exists: {model.id} v{model.version}")
        self._models[key] = model

    def get(self, model_id: str, version: int | None = None) -> FundModelDefinition:
        if version is not None:
            model = self._models.get((model_id, version))
            if model is None:
                raise KeyError(f"Fund model not found: {model_id} v{version}")
            return model

        versions = [model for (mid, _), model in self._models.items() if mid == model_id]
        if not versions:
            raise KeyError(f"Fund model not found: {model_id}")
        return max(versions, key=lambda item: item.version)

    def list_models(self) -> list[FundModelDefinition]:
        return sorted(self._models.values(), key=lambda item: (item.id, item.version))

    def get_entity(self, model_id: str, entity_name: str, version: int | None = None) -> EntityDefinition:
        model = self.get(model_id, version)
        for entity in model.entities:
            if entity.name == entity_name:
                return entity
        raise KeyError(f"Entity not found: {entity_name}")
