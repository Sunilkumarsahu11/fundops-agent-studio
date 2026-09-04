from typing import Any

from app.agent_runtime.models import AgentDefinition, RetryPolicy, ToolDefinition, WorkflowStep
from app.agent_runtime.registry import ToolRegistry

from .models import AgentBlueprint, BlueprintStatus, FactoryRequest, FactoryValidation, ToolSelection


class AgentFactory:
    """Build declarative agents using only allow-listed registered tools."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.blueprints: dict[str, AgentBlueprint] = {}

    def draft(self, request: FactoryRequest) -> AgentBlueprint:
        text = request.request.lower()
        selections: list[ToolSelection] = []
        steps: list[WorkflowStep] = []
        if any(word in text for word in ("reconcile", "reconciliation", "compare")):
            self._add(selections, steps, "reconcile_records", "Deterministic reconciliation of two supplied canonical datasets.", {"left_records": "$left_records", "right_records": "$right_records", "key_fields": "$key_fields", "amount_field": "$amount_field", "date_field": "$date_field", "currency_field": "$currency_field", "amount_tolerance": "$amount_tolerance", "amount_tolerance_percent": "$amount_tolerance_percent", "date_tolerance_days": "$date_tolerance_days", "materiality_threshold": "$materiality_threshold"})
            if any(word in text for word in ("exception", "exceptions", "flag", "report")):
                self._add(selections, steps, "build_exception_report", "Produces the evidence-backed exception report.", {"reconciliation_result": "$step_1"})
            if any(word in text for word in ("evidence", "audit", "govern")):
                self._add(selections, steps, "collect_evidence", "Collects source provenance.", {"records": "$left_records"})
        elif any(word in text for word in ("capital call", "capital calls", "capital-call")):
            self._add(selections, steps, "capital_call_review", "Runs deterministic capital-call controls.", {"records": "$records"})
        elif any(word in text for word in ("nav review", "nav check", "review nav", "net asset value")):
            self._add(selections, steps, "nav_review", "Runs deterministic NAV controls.", {"records": "$records", "variance_percent_threshold": "$variance_percent_threshold"})
        elif any(word in text for word in ("valuation review", "valuation check", "review valuation", "valuations")):
            self._add(selections, steps, "valuation_review", "Runs deterministic valuation controls.", {"records": "$records", "allowed_currencies": "$allowed_currencies"})
        elif any(word in text for word in ("portfolio exposure", "portfolio concentration", "exposure analysis", "investment exposure")):
            self._add(selections, steps, "portfolio_exposure", "Aggregates investment exposure deterministically.", {"records": "$records", "group_field": "$group_field", "amount_field": "$amount_field"})
        elif any(word in text for word in ("investor reporting", "investor report", "investor statement", "investor reporting dataset")):
            self._add(selections, steps, "investor_reporting", "Builds deterministic investor reporting totals.", {"records": "$records", "investor_field": "$investor_field", "metric_fields": "$metric_fields"})
        elif any(word in text for word in ("excel quality", "workbook quality", "quality check", "spreadsheet quality")):
            self._add(selections, steps, "excel_quality", "Inspects workbook structure and quality risks.", {"file_name": "$file_name", "content_base64": "$content_base64", "source_format": "$source_format", "min_columns": "$min_columns", "min_rows": "$min_rows"})
        elif any(word in text for word in ("normalize", "normalization", "canonicalize")):
            self._add(selections, steps, "normalization_review", "Normalizes canonical records using the configured model.", {"records": "$records", "model_id": "$model_id", "model_version": "$model_version"})
        elif any(word in text for word in ("exception investigation", "investigate exception", "prioritize exceptions", "triage exceptions", "exception triage")):
            self._add(selections, steps, "exception_investigation", "Prioritizes existing exceptions without changing outcomes.", {"exceptions": "$exceptions", "default_severity": "$default_severity"})
        elif any(word in text for word in ("ingest", "import", "load", "workbook", "excel", "json")):
            self._add(selections, steps, "inspect_source", "Inspects source structure before ingestion.", {"file_name": "$file_name", "content_base64": "$content_base64", "source_format": "$source_format"})
            if any(word in text for word in ("ingest", "import", "load")):
                self._add(selections, steps, "ingest_source", "Loads the inspected source into the canonical fund model.", {"file_name": "$file_name", "content_base64": "$content_base64", "source_format": "$source_format", "model_id": "$model_id", "model_version": "$model_version"})
        if not steps:
            selections.append(ToolSelection(tool="echo", reason="Safe fallback for unsupported requests.", confidence=0.2))
            steps.append(WorkflowStep(id="step_1", tool="echo", input={"request": request.request}))
        blueprint = AgentBlueprint(name=request.name or self._name(request.request), description=f"Generated from: {request.request}", source_request=request.request, tools=selections, steps=steps, inputs=request.inputs, metadata={"planner": "deterministic", "governance": "allow-listed-tools-only", "context_references": "$step_n / $input_name"})
        self.blueprints[str(blueprint.id)] = blueprint
        return blueprint

    def validate(self, blueprint: AgentBlueprint) -> FactoryValidation:
        errors: list[str] = []
        warnings: list[str] = []
        seen: set[str] = set()
        financial_tools = {"reconcile_records", "build_exception_report", "calculate_variance", "evaluate_materiality", "capital_call_review", "nav_review", "valuation_review", "portfolio_exposure", "investor_reporting"}
        for step in blueprint.steps:
            if step.id in seen: errors.append(f"Duplicate step id: {step.id}")
            seen.add(step.id)
            if not self.registry.has(step.tool): errors.append(f"Unknown tool: {step.tool}")
            definition = self.registry.get(step.tool)
            if definition and definition.deterministic and step.tool in financial_tools and not step.required: errors.append(f"Financial control step must be required: {step.id}")
        if not blueprint.steps: errors.append("Blueprint must contain at least one step")
        if any(selection.confidence < 0.8 for selection in blueprint.tools): warnings.append("One or more tool selections have low confidence and should be reviewed.")
        return FactoryValidation(valid=not errors, errors=errors, warnings=warnings)

    def publish(self, blueprint: AgentBlueprint, approved_by: str) -> AgentDefinition:
        if not approved_by.strip(): raise ValueError("approved_by is required")
        validation = self.validate(blueprint)
        if not validation.valid: raise ValueError("Cannot publish invalid blueprint: " + "; ".join(validation.errors))
        blueprint.status = BlueprintStatus.PUBLISHED
        blueprint.metadata["approved_by"] = approved_by
        blueprint.metadata["approval_required"] = True
        self.blueprints[str(blueprint.id)] = blueprint
        return AgentDefinition(id=f"generated-{blueprint.id}", name=blueprint.name, description=blueprint.description, steps=blueprint.steps)

    def get(self, blueprint_id: str) -> AgentBlueprint | None: return self.blueprints.get(blueprint_id)

    def _add(self, selections: list[ToolSelection], steps: list[WorkflowStep], tool: str, reason: str, input: dict[str, Any] | None = None) -> None:
        if not self.registry.has(tool): return
        selections.append(ToolSelection(tool=tool, reason=reason, confidence=0.95))
        definition: ToolDefinition | None = self.registry.get(tool)
        steps.append(WorkflowStep(id=f"step_{len(steps)+1}", tool=tool, input=input or {}, required=True, timeout_seconds=definition.timeout_seconds if definition else 30, retry_policy=definition.retry_policy if definition else RetryPolicy()))

    @staticmethod
    def _name(request: str) -> str:
        return " ".join(request.strip().split()[:7]).rstrip(".,") or "Generated FundOps Agent"
