from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Provenance(BaseModel):
    source_file: str | None = None
    source_sheet: str | None = None
    source_cell: str | None = None
    source_path: str | None = None
    source_field: str | None = None
    ingestion_run_id: UUID | None = None


class CanonicalRecord(BaseModel):
    record_id: UUID = Field(default_factory=uuid4)
    model_id: str
    model_version: int
    entity: str
    data: dict[str, Any] = Field(default_factory=dict)
    provenance: list[Provenance] = Field(default_factory=list)
    tenant_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def source_evidence(self) -> list[dict[str, Any]]:
        return [item.model_dump(mode="json", exclude_none=True) for item in self.provenance]
