from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from app.fund_model.records import CanonicalRecord, Provenance
from app.fund_model.schema import FundModelDefinition

from .excel import read_excel
from .json_reader import read_json
from .mapper import suggest_mappings
from .models import IngestionResult, SourceFormat
from .normalizer import normalize_value


def inspect_source(file_name: str, content: bytes, source_format: SourceFormat):
    if source_format == SourceFormat.EXCEL:
        return read_excel(content, file_name)
    return read_json(json.loads(content.decode("utf-8")), file_name)


def ingest(
    file_name: str,
    content: bytes,
    source_format: SourceFormat,
    model: FundModelDefinition,
    tenant_id: str | None = None,
    ingestion_run_id: UUID | None = None,
) -> IngestionResult:
    run_id = ingestion_run_id or uuid4()
    tables = inspect_source(file_name, content, source_format)
    mapping = suggest_mappings(tables, model)
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for table in tables:
        source_columns = {column.name for column in table.columns}
        table_maps = [
            candidate
            for candidate in mapping.candidates
            if candidate.source_field in source_columns
        ]
        grouped: dict[str, list[Any]] = {}
        for candidate in table_maps:
            grouped.setdefault(candidate.target_entity, []).append(candidate)
        for entity_name, entity_maps in grouped.items():
            entity = next(entity for entity in model.entities if entity.name == entity_name)
            for row_index, row in enumerate(table.rows, start=1):
                data: dict[str, Any] = {}
                provenance: list[Provenance] = []
                for candidate in entity_maps:
                    field = next(
                        field
                        for field in entity.fields
                        if field.name == candidate.target_field
                    )
                    raw = row.get(candidate.source_field)
                    try:
                        data[field.name] = normalize_value(raw, field.type.value)
                    except ValueError as exc:
                        warnings.append(
                            f"{table.name} row {row_index} field "
                            f"{candidate.source_field}: {exc}"
                        )
                        continue
                    source_column = next(
                        column
                        for column in table.columns
                        if column.name == candidate.source_field
                    )
                    source_cell = None
                    if source_column.source.cell:
                        column_letters = "".join(
                            char
                            for char in source_column.source.cell
                            if char.isalpha()
                        )
                        source_cell = f"{column_letters}{row_index + 1}"
                    provenance.append(
                        Provenance(
                            source_file=file_name,
                            source_sheet=source_column.source.sheet,
                            source_cell=source_cell,
                            source_path=source_column.source.path,
                            source_field=candidate.source_field,
                            ingestion_run_id=run_id,
                        )
                    )
                if data:
                    records.append(
                        CanonicalRecord(
                            model_id=model.id,
                            model_version=model.version,
                            entity=entity.name,
                            data=data,
                            provenance=provenance,
                            tenant_id=tenant_id,
                        ).model_dump(mode="json")
                    )
    return IngestionResult(
        ingestion_run_id=run_id,
        tables=tables,
        mapping=mapping,
        records=records,
        warnings=warnings,
    )
