from __future__ import annotations

from typing import Any

from .models import SourceColumn, SourceLocation, SourceTable
from .type_inference import infer_type


def read_json(payload: Any, file_name: str) -> list[SourceTable]:
    tables: list[SourceTable] = []
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        tables.append(_table("root", payload, file_name, "$"))
        return tables
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                tables.append(_table(key, value, file_name, f"$.{key}"))
        if not tables:
            tables.append(_table("root", [payload], file_name, "$"))
        return tables
    raise ValueError("JSON root must be an object or an array of objects")


def _table(name: str, rows: list[dict[str, Any]], file_name: str, path: str) -> SourceTable:
    names = list(dict.fromkeys(key for row in rows for key in row))
    columns = [SourceColumn(name=key, sample_values=[row.get(key) for row in rows[:10]], inferred_type=infer_type([row.get(key) for row in rows]), nullable=any(row.get(key) is None for row in rows), source=SourceLocation(file_name=file_name, path=f"{path}[*].{key}")) for key in names]
    return SourceTable(name=name, columns=columns, rows=rows, source=SourceLocation(file_name=file_name, path=path))
