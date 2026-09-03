from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SourceFormat(str, Enum):
    EXCEL = "excel"
    JSON = "json"


class SourceLocation(BaseModel):
    file_name: str
    sheet: str | None = None
    cell: str | None = None
    path: str | None = None


class SourceColumn(BaseModel):
    name: str
    sample_values: list[Any] = Field(default_factory=list)
    inferred_type: str = "string"
    nullable: bool = True
    source: SourceLocation


class SourceTable(BaseModel):
    name: str
    columns: list[SourceColumn] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    source: SourceLocation


class IngestionRequest(BaseModel):
    file_name: str
    content: bytes
    format: SourceFormat
    model_id: str
    model_version: int | None = None
    tenant_id: str | None = None
    ingestion_run_id: UUID = Field(default_factory=uuid4)


class MappingCandidate(BaseModel):
    source_field: str
    target_entity: str
    target_field: str
    confidence: float = Field(ge=0, le=1)
    reason: str
    requires_review: bool = False


class UnmappedField(BaseModel):
    source_field: str
    reason: str


class MappingResult(BaseModel):
    model_id: str
    model_version: int
    candidates: list[MappingCandidate] = Field(default_factory=list)
    unmapped: list[UnmappedField] = Field(default_factory=list)


class IngestionResult(BaseModel):
    ingestion_run_id: UUID
    tables: list[SourceTable] = Field(default_factory=list)
    mapping: MappingResult | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
