from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.fund_model.records import CanonicalRecord


class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    MATCHED_WITHIN_TOLERANCE = "matched_within_tolerance"
    MISMATCH = "mismatch"
    MISSING_LEFT = "missing_left"
    MISSING_RIGHT = "missing_right"
    DUPLICATE = "duplicate"
    REVIEW = "review"


class ReasonCode(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    AMOUNT_VARIANCE = "AMOUNT_VARIANCE"
    DATE_VARIANCE = "DATE_VARIANCE"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    SIGN_MISMATCH = "SIGN_MISMATCH"
    MISSING_LEFT = "MISSING_LEFT"
    MISSING_RIGHT = "MISSING_RIGHT"
    DUPLICATE_LEFT = "DUPLICATE_LEFT"
    DUPLICATE_RIGHT = "DUPLICATE_RIGHT"
    AGGREGATION_VARIANCE = "AGGREGATION_VARIANCE"
    LOW_CONFIDENCE_MATCH = "LOW_CONFIDENCE_MATCH"


class ReconciliationRequest(BaseModel):
    left_records: list[CanonicalRecord]
    right_records: list[CanonicalRecord]
    key_fields: list[str] = Field(min_length=1)
    amount_field: str | None = None
    date_field: str | None = None
    currency_field: str | None = None
    amount_tolerance: float = Field(default=0.0, ge=0)
    amount_tolerance_percent: float = Field(default=0.0, ge=0)
    date_tolerance_days: int = Field(default=0, ge=0)
    materiality_threshold: float = Field(default=0.0, ge=0)
    enable_fuzzy_matching: bool = False
    fuzzy_threshold: float = Field(default=0.9, ge=0, le=1)


class RecordMatch(BaseModel):
    match_id: UUID = Field(default_factory=uuid4)
    left_record_id: UUID | None = None
    right_record_id: UUID | None = None
    status: ReconciliationStatus
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    match_confidence: float = Field(default=1.0, ge=0, le=1)
    amount_left: float | None = None
    amount_right: float | None = None
    amount_variance: float | None = None
    amount_variance_percent: float | None = None
    date_left: str | None = None
    date_right: str | None = None
    currency_left: str | None = None
    currency_right: str | None = None
    materiality: str = "immaterial"
    evidence: dict[str, Any] = Field(default_factory=dict)


class ReconciliationSummary(BaseModel):
    total_left: int
    total_right: int
    matched: int
    matched_within_tolerance: int
    mismatched: int
    missing_left: int
    missing_right: int
    duplicates: int
    review: int
    total_absolute_variance: float
    material_variance_count: int


class ReconciliationResult(BaseModel):
    reconciliation_id: UUID = Field(default_factory=uuid4)
    status: str
    summary: ReconciliationSummary
    matches: list[RecordMatch] = Field(default_factory=list)
