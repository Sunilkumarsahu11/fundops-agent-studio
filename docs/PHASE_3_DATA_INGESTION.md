# Phase 3 — Data Ingestion & Schema Mapping

## Objective
Convert heterogeneous Excel and JSON inputs into validated, provenance-preserving `CanonicalRecord` objects without silently losing source data.

## Pipeline

```text
Excel / JSON
    ↓
source inspection
    ↓
sheet/table/header discovery
    ↓
type inference
    ↓
schema mapping suggestions
    ↓
deterministic normalization
    ↓
CanonicalRecord + provenance
    ↓
Phase 2 model validation
```

## Supported inputs

- `.xlsx`, `.xlsm`, `.xltx`, `.xltm` via OpenPyXL
- JSON objects and arrays of objects
- Nested JSON arrays under object keys are exposed as separate logical tables

## Mapping strategy

The initial mapper is deterministic and produces candidates with confidence and reasons. Low-confidence mappings require review. Unmapped source columns are explicitly returned rather than discarded.

The mapper is intentionally separated from the future LLM layer. In later phases, an LLM can propose semantic mappings, while the deterministic mapper validates the proposal against the active fund model.

## Normalization

Supported deterministic conversions include:

- string
- integer
- number
- money
- boolean
- date
- datetime

Financial calculations are not performed by the LLM or ingestion mapper.

## Provenance

Every generated canonical record can retain:

- source file;
- source sheet;
- source cell or JSON path;
- original source field;
- ingestion run ID;
- fund model ID/version;
- tenant ID.

## API

`POST /ingestion/inspect` inspects a file and returns discovered tables, columns and inferred types.

`POST /ingestion/run` executes ingestion against a selected fund model version and returns mapping, records and warnings.

## Safety rules

1. Never silently drop unmapped fields.
2. Never overwrite the original source file.
3. Never change an active fund model during ingestion.
4. Every canonical record carries the model version that interpreted it.
5. Low-confidence mapping is reviewable.
6. Type-conversion failures become warnings rather than fabricated values.

## Phase 3 exit criteria

- Excel ingestion: complete.
- JSON ingestion: complete.
- Header/table discovery: complete.
- Type inference: complete.
- Schema mapping: complete for deterministic baseline.
- Normalization: complete for initial field types.
- Provenance: complete at canonical-record boundary.
- Ingestion API: complete.
- Automated tests: added.

## Next phase

Phase 4 builds the deterministic reconciliation engine on top of these canonical records: exact/fuzzy entity matching, amount/date/currency checks, tolerances, missing/duplicate detection, sign checks, aggregation checks and evidence-backed exception reports.
