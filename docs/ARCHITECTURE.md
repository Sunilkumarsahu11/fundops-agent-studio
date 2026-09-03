# FundOps Agent Studio — Architecture

## 1. Architectural goal

Build a reusable platform where a fund manager can describe an operational task in natural language and the system converts it into a governed workflow composed of deterministic tools and AI reasoning.

The platform must support many fund-operation agents without creating a separate application for each task.

## 2. Logical architecture

```text
                    +----------------------+
                    |   React Agent Studio |
                    +----------+-----------+
                               |
                         REST / JSON
                               |
                    +----------v-----------+
                    |      FastAPI API      |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |    Agent Factory      |
                    | intent / planning /    |
                    | workflow generation   |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |    Agent Runtime      |
                    | state / execution /   |
                    | validation / retry    |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |     Tool Registry     |
                    +--+------+------+------+ 
                       |      |      |      |
                     Excel   JSON  Reconcile Rules
                       |      |      |      |
                       +------+------+------+
                              |
                    +---------v----------+
                    | Canonical Fund Data |
                    +---------+----------+
                              |
                    +---------v----------+
                    |    PostgreSQL      |
                    +--------------------+

              +---------------------------+
              | Evidence / Audit / HITL   |
              +---------------------------+
```

## 3. Separation of responsibilities

### LLM layer

The LLM is responsible for tasks where semantic reasoning is useful:

- understand the user's request;
- classify the fund-operation task;
- identify required inputs;
- map source columns to canonical fields;
- select or propose tools;
- generate explanations;
- summarize exceptions.

The LLM must not be the source of truth for arithmetic, reconciliation totals or financial rules.

### Deterministic tool layer

Python services perform:

- Excel and JSON parsing;
- type and schema validation;
- entity matching;
- date/currency normalization;
- arithmetic;
- tolerance comparisons;
- reconciliation;
- financial validation rules;
- report generation.

This separation reduces hallucination risk and makes results testable.

## 4. Agent lifecycle

```text
RECEIVE
   |
UNDERSTAND
   |
PLAN
   |
EXECUTE
   |
VALIDATE
   |
EXPLAIN
   |
HUMAN APPROVAL (when required)
   |
COMPLETE
```

Every stage should emit structured execution events so an individual run can be inspected later.

## 5. Agent Factory

The Agent Factory turns a natural-language request into a declarative workflow.

Example request:

> Check our quarterly portfolio Excel against valuation JSON and identify anything that could affect NAV.

The factory should derive:

- task type: reconciliation + valuation/NAV risk;
- inputs: Excel + JSON;
- entities: portfolio company, investment, valuation;
- operations: ingest → map → normalize → reconcile → validate → rank → explain;
- outputs: exceptions + evidence + report;
- approval policy: human review for material exceptions.

The generated workflow is validated before execution.

## 6. Workflow model

Agents should be represented as configuration rather than arbitrary generated code.

```yaml
id: capital-call-validator
input:
  - investor_commitments
  - capital_calls
steps:
  - tool: normalize_entities
  - tool: calculate_remaining_commitment
  - tool: validate_commitment_limit
  - tool: generate_exceptions
output:
  format: report
```

The runtime executes the workflow using registered tools.

## 7. Canonical fund model

The initial domain model contains:

- Fund
- FundPeriod
- Investor
- Commitment
- CapitalCall
- Distribution
- PortfolioCompany
- Investment
- Valuation
- Transaction
- NAV
- Currency

Source-specific data is mapped into this model while retaining source lineage.

## 8. Evidence model

Every material output should have evidence such as:

```text
source_file
source_sheet
source_cell / source_row
source_json_path
canonical_field
observed_value
expected_value
rule_id
execution_id
```

Example:

```text
portfolio_q2.xlsx
Portfolio
H42
valuation
12500000
12800000
NAV_VALUATION_MATCH
run-123
```

This allows a fund manager to move from an exception directly to its source.

## 9. Human-in-the-loop

Human approval is required when an agent:

- proposes a material financial adjustment;
- changes canonical data;
- publishes an external report;
- encounters ambiguous mappings above a configured risk threshold.

Read-only analysis can normally complete automatically.

## 10. Security and tenancy direction

The hackathon MVP can use a single tenant and local development credentials. The production design should support:

- tenant isolation;
- RBAC;
- SSO/OIDC;
- encryption at rest and in transit;
- secrets management;
- immutable audit events;
- input/output retention policies;
- prompt-injection and malicious-file controls.

## 11. Deliberate non-goals for Phase 0

Do not introduce Kafka, Kubernetes, service meshes or a fleet of microservices at this stage. The objective is a fast, testable modular monolith that can evolve later if scale requires it.
