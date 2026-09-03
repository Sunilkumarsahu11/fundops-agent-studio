# Phase 2 — Configurable Fund Data Model

## Status

**Complete.** Phase 2 is now a metadata-driven, versioned schema registry with PostgreSQL persistence, canonical records, provenance, JSON Schema generation, validation, schema diff/migration planning, and tenant/client overlays.

## Design decision

The canonical fund model is **metadata-driven**, not hard-coded into Python classes.

```text
FundModelDefinition
 ├── id / version / status
 ├── EntityDefinition[]
 │    ├── FieldDefinition[]
 │    └── RelationshipDefinition[]
 └── metadata
```

This allows fund managers or administrators to introduce fields, entities, validation rules and relationships without changing application code.

## Version lifecycle

Versions are immutable once created by policy. A change creates a new version; activation retires the previous active version:

```text
private-markets-core v1  → retired
private-markets-core v2  → active
private-markets-core v3  → draft
```

Historical records retain the model id/version that interpreted them. This prevents schema changes from silently changing historical meaning.

## PostgreSQL persistence

The registry persists both the complete definition and queryable metadata in:

- `fund_models`
- `fund_model_versions`
- `entity_definitions`
- `field_definitions`
- `relationship_definitions`

Alembic migration `0001_fund_model_registry` creates these tables. The canonical definition is retained as JSON so the registry can evolve without requiring an application-code deployment for every client-specific field.

Run migrations from `backend` with:

```bash
alembic upgrade head
```

## Schema Registry API

- `POST /fund-models` — create a model/version
- `GET /fund-models` — list versions
- `GET /fund-models/{id}` — get a version; omit `version` for latest
- `GET /fund-models/{id}/versions` — list all versions
- `POST /fund-models/{id}/versions` — create a new version
- `POST /fund-models/{id}/versions/{version}/activate` — activate and retire the previous active version
- `GET /fund-models/{id}/schema` — generate JSON Schema
- `GET /fund-models/{id}/diff?from_version=1&to_version=2` — compare versions
- `GET /fund-models/{id}/migration-plan?...` — produce a reviewable migration plan
- `POST /fund-models/{id}/validate-record` — validate a canonical record
- `POST /fund-models/{id}/overlay?base_version=1` — create a client/tenant-specific composed model
- `POST /fund-models/bootstrap` — seed the starter private-markets model

## Canonical record envelope

Normalized operational data uses a stable envelope:

```json
{
  "record_id": "uuid",
  "model_id": "private-markets-core",
  "model_version": 2,
  "entity": "Valuation",
  "data": {
    "valuation_id": "VAL-1001",
    "valuation_date": "2026-06-30",
    "value": 12500000,
    "currency": "GBP"
  },
  "provenance": [
    {
      "source_file": "q2_valuation.xlsx",
      "source_sheet": "Portfolio",
      "source_cell": "H27",
      "source_field": "Fair Value",
      "ingestion_run_id": "uuid"
    }
  ]
}
```

This gives downstream reconciliation and agent explanations a source-evidence trail.

## JSON Schema generation

`FundModelDefinition` can be converted into JSON Schema, including field types, enum constraints, descriptions, validation metadata, required fields, model id and version.

## Validation

Canonical records are checked against their exact model version. Validation detects:

- unknown entities/fields;
- missing required fields;
- illegal nulls;
- invalid primitive types;
- invalid enum values;
- invalid references/JSON shapes.

Business calculations such as NAV, IRR and reconciliation tolerances remain deterministic application logic rather than LLM-generated logic.

## Schema diff and migration planning

Diffs classify changes as low/medium/high risk. High-risk changes include removing entities/fields, changing field types, and making an existing field required.

Migration plans are intentionally **review-only**. The system does not silently mutate financial data. A future migration executor can require explicit human approval before applying transformations/backfills.

## Tenant/client overlays

A tenant-specific model can inherit the base model and add or override entities, fields, relationships and metadata. The resulting model records its base model id/version so lineage remains explicit.

Tenant identity is carried through `metadata.tenant_id` and the `X-Tenant-ID` API header in this hackathon implementation. Production deployment should replace this with authenticated tenant context and enforce tenant isolation at the persistence layer.

## Safe evolution rules

Prefer:

- adding optional fields;
- adding enum values;
- adding validation metadata;
- adding relationships;
- deprecating fields in a new version.

Require a new version plus migration/reprocessing review for:

- semantic changes;
- monetary unit/sign convention changes;
- identity-key changes;
- relationship cardinality changes;
- required/nullable changes affecting existing data.

## Exit criteria

Phase 2 delivers the configurable foundation required by Phase 3 ingestion and Phase 4 reconciliation. The ingestion layer can now resolve a model version, validate normalized records, preserve provenance, and generate machine-readable schemas without hard-coding every client's fund structure.
