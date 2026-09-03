# Phase 2 — Configurable Fund Data Model

## Design decision

The canonical fund model is **metadata-driven**, not hard-coded into Python classes.

A fund model consists of:

```text
FundModelDefinition
 ├── version
 ├── status
 ├── EntityDefinition[]
 │    ├── FieldDefinition[]
 │    └── RelationshipDefinition[]
 └── metadata
```

This allows a fund manager or administrator to introduce fields, entities, validation rules and relationships without changing application code.

## Versioning

Models are immutable by version once activated. A change creates a new version:

```text
private-markets-core v1  → active
private-markets-core v2  → draft
private-markets-core v3  → future
```

Existing data remains associated with the model version that interpreted it. This prevents a schema change from silently changing historical meaning.

## Field types

Supported initial types:

- string
- integer
- number
- boolean
- date
- datetime
- money
- enum
- reference
- json

The `validation` object is intentionally extensible for constraints such as min/max, regex, precision, currency rules or domain-specific validation.

## Relationships

Relationships are metadata too. For example:

```text
CapitalCall → Commitment → Investor
Investment  → Fund
Valuation   → Investment
```

The application can therefore inspect the graph without hard-coding every relationship.

## Storage strategy

For the hackathon, the canonical definition should be stored as versioned schema metadata. Operational records can use JSONB-backed payloads initially, with relational indexes/columns added only where query or reconciliation performance requires them.

This avoids the two extremes:

- hard-coded tables that require migrations for every client-specific field;
- a completely opaque EAV model that makes analytics and validation painful.

## Source provenance

Every normalized record should eventually carry provenance such as:

```json
{
  "source_file": "q2_valuation.xlsx",
  "source_sheet": "Portfolio",
  "source_cell": "H27",
  "source_field": "Fair Value",
  "ingestion_run_id": "...",
  "model_id": "private-markets-core",
  "model_version": 2
}
```

Provenance belongs to the normalized data layer, not inside the business field definition itself.

## Safe schema evolution

Allowed changes should include:

- add optional field;
- add new enum value;
- add metadata/validation;
- add relationship;
- deprecate field for future versions;
- rename a field through an explicit migration mapping.

Dangerous changes require a new model version and migration/reprocessing plan:

- changing a field's semantic meaning;
- changing a monetary unit or sign convention;
- changing an entity's identity key;
- changing relationship cardinality;
- changing required/nullable semantics for existing data.

## Next Phase 2 work

1. Persist model definitions and versions in PostgreSQL.
2. Add schema registry APIs.
3. Add canonical record envelope and provenance.
4. Add JSON Schema generation from `FundModelDefinition`.
5. Add migration/diff tooling between model versions.
6. Add validation of records against the active model.
7. Add tenant/client-specific model overlays.
