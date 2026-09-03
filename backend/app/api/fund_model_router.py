from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.fund_model.persistence import FundModelStore
from app.fund_model.service import FundModelService
from app.fund_model.schema import FundModelDefinition
from app.fund_model.records import CanonicalRecord
from app.fund_model.validation import validate_record
from app.fund_model.migration import migration_plan

router = APIRouter(prefix="/fund-models", tags=["fund-models"])
service = FundModelService(FundModelStore(get_settings().database_url))


@router.post("", response_model=FundModelDefinition)
def create_model(model: FundModelDefinition, x_tenant_id: str | None = Header(default=None)):
    if x_tenant_id:
        model.metadata["tenant_id"] = x_tenant_id
    try:
        return service.create(model)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/bootstrap", response_model=FundModelDefinition)
def bootstrap_default():
    try:
        return service.bootstrap_default()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.get("", response_model=list[FundModelDefinition])
def list_models(x_tenant_id: str | None = Header(default=None)):
    try:
        models = service.store.list()
        if x_tenant_id:
            models = [m for m in models if m.metadata.get("tenant_id") in (None, x_tenant_id)]
        return models
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.get("/{model_id}", response_model=FundModelDefinition)
def get_model(model_id: str, version: int | None = None):
    try:
        model = service.store.get(model_id, version)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    if model is None:
        raise HTTPException(status_code=404, detail="Fund model not found")
    return model


@router.get("/{model_id}/versions", response_model=list[FundModelDefinition])
def list_versions(model_id: str):
    try:
        return service.store.list(model_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc


@router.post("/{model_id}/versions", response_model=FundModelDefinition)
def create_version(model_id: str, model: FundModelDefinition):
    try:
        return service.create_version(model_id, model)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{model_id}/versions/{version}/activate", response_model=FundModelDefinition)
def activate_version(model_id: str, version: int):
    try:
        return service.activate(model_id, version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{model_id}/schema")
def get_json_schema(model_id: str, version: int | None = None):
    try:
        return service.schema(model_id, version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{model_id}/diff")
def compare_versions(model_id: str, from_version: int, to_version: int):
    try:
        return service.diff(model_id, from_version, to_version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{model_id}/migration-plan")
def get_migration_plan(model_id: str, from_version: int, to_version: int):
    try:
        old = service.store.get(model_id, from_version)
        new = service.store.get(model_id, to_version)
        if old is None or new is None:
            raise KeyError("Both model versions must exist")
        return migration_plan(old, new)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{model_id}/validate-record")
def validate_model_record(model_id: str, record: CanonicalRecord, version: int | None = None):
    try:
        model = service.store.get(model_id, version)
        if model is None:
            raise KeyError("Fund model not found")
        errors = validate_record(record, model)
        return {"valid": not errors, "errors": errors, "model": {"id": model.id, "version": model.version}}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{model_id}/overlay", response_model=FundModelDefinition)
def create_overlay(model_id: str, base_version: int, overlay: FundModelDefinition, x_tenant_id: str | None = Header(default=None)):
    if x_tenant_id:
        overlay.metadata["tenant_id"] = x_tenant_id
    try:
        return service.overlay(model_id, base_version, overlay)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
