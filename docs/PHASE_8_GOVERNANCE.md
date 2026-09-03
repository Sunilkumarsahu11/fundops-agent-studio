# Phase 8 — Evidence, Audit & Human-in-the-Loop

## Objective

Make every agent run reviewable: preserve a run snapshot, expose execution audit events, surface source evidence, and require an explicit approval record for consequential actions.

## Implemented

- `AuditEvent` immutable append-only projection with run, agent, actor, action and timestamp.
- `RunSnapshot` captures the request, output, agent/version and final status at execution time.
- `EvidenceItem` models file/sheet/cell/JSON-path/source-field evidence linked to a run.
- Evidence extraction walks run outputs and preserves provenance emitted by the canonical data model.
- `ApprovalRequest` and `ApprovalDecision` support pending/approved/rejected human decisions.
- Double decisions are rejected; approvals require a captured run snapshot.
- FastAPI endpoints under `/governance` for audit, evidence, snapshots and approvals.
- Runtime API execution now automatically captures governance information after every run.

## Endpoints

```text
GET  /governance/runs/{run_id}/audit
GET  /governance/runs/{run_id}/evidence
GET  /governance/runs/{run_id}/snapshot
POST /governance/approvals
GET  /governance/approvals/{approval_id}
POST /governance/approvals/{approval_id}/approve
POST /governance/approvals/{approval_id}/reject
```

## Governance boundary

The current implementation is intentionally an in-memory persistence boundary, consistent with the existing Phase 1 runtime store. It does not claim durable compliance storage. A later persistence adapter can map these immutable projections to PostgreSQL without changing the API contract.

The system does not automatically approve actions. An approval is a separate, auditable decision object and cannot be silently overwritten or decided twice.
