from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from app.core.config import get_settings
from app.fund_model.persistence import FundModelStore
from app.ingestion.models import SourceFormat
from app.ingestion.pipeline import ingest, inspect_source

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
store = FundModelStore(get_settings().database_url)


@router.post("/inspect")
async def inspect(file: UploadFile = File(...), source_format: SourceFormat | None = Form(default=None)):
    content = await file.read()
    fmt = source_format or _format_from_name(file.filename or "")
    try:
        return {"file_name": file.filename, "format": fmt, "tables": inspect_source(file.filename or "upload", content, fmt)}
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run")
async def run_ingestion(model_id: str = Form(...), file: UploadFile = File(...), model_version: int | None = Form(default=None), source_format: SourceFormat | None = Form(default=None), x_tenant_id: str | None = Header(default=None)):
    content = await file.read()
    fmt = source_format or _format_from_name(file.filename or "")
    model = store.get(model_id, model_version)
    if model is None:
        raise HTTPException(status_code=404, detail="Fund model not found")
    run_id = uuid4()
    try:
        return ingest(file.filename or "upload", content, fmt, model, tenant_id=x_tenant_id, ingestion_run_id=run_id)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _format_from_name(file_name: str) -> SourceFormat:
    lower = file_name.lower()
    if lower.endswith((".xlsx", ".xlsm", ".xltx", ".xltm")):
        return SourceFormat.EXCEL
    if lower.endswith(".json"):
        return SourceFormat.JSON
    raise HTTPException(status_code=400, detail="Unable to determine source format; provide source_format")
