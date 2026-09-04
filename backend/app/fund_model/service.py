from __future__ import annotations

from .default_model import default_fund_model
from .diff import diff_models
from .json_schema import model_to_json_schema
from .overlay import apply_overlay
from .persistence import FundModelStore
from .schema import FundModelDefinition


class FundModelService:
    def __init__(self, store: FundModelStore) -> None:
        self.store = store

    def bootstrap_default(self) -> FundModelDefinition:
        model = default_fund_model()
        if self.store.get(model.id, model.version) is None:
            self.store.save(model)
        return model

    def create(self, model: FundModelDefinition) -> FundModelDefinition:
        self.store.save(model)
        return model

    def create_version(self, model_id: str, model: FundModelDefinition) -> FundModelDefinition:
        current = self.store.get(model_id)
        if current is None:
            raise KeyError(f"Fund model not found: {model_id}")
        if model.id != model_id:
            raise ValueError("Model id cannot change when creating a version")
        if model.version <= current.version:
            model.version = self.store.next_version(model_id)
        self.store.save(model)
        return model

    def activate(self, model_id: str, version: int) -> FundModelDefinition:
        target = self.store.get(model_id, version)
        if target is None:
            raise KeyError(f"Fund model not found: {model_id} v{version}")
        self.store.activate(model_id, version)
        return self.store.get(model_id, version)  # type: ignore[return-value]

    def schema(self, model_id: str, version: int | None = None) -> dict:
        model = self.store.get(model_id, version)
        if model is None:
            raise KeyError(f"Fund model not found: {model_id}")
        return model_to_json_schema(model)

    def diff(self, model_id: str, from_version: int, to_version: int) -> dict:
        old = self.store.get(model_id, from_version)
        new = self.store.get(model_id, to_version)
        if old is None or new is None:
            raise KeyError("Both model versions must exist")
        return diff_models(old, new)

    def overlay(self, base_id: str, base_version: int, overlay_model: FundModelDefinition) -> FundModelDefinition:
        base = self.store.get(base_id, base_version)
        if base is None:
            raise KeyError("Base model not found")
        composed = apply_overlay(base, overlay_model)
        self.store.save(composed)
        return composed
