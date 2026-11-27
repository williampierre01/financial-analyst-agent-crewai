"""Explicit HTTP contracts, including the existing financial v3 snapshot."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

from financial_data import normalize_ticker


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticker: str = Field(min_length=1, max_length=16, strict=True)

    @field_validator("ticker")
    @classmethod
    def b3_ticker(cls, value: str) -> str:
        return normalize_ticker(value)


class Quote(BaseModel):
    price: FiniteFloat = Field(gt=0)
    currency: Literal["BRL"]
    source: Literal["yfinance"]
    as_of: datetime | None
    freshness: Literal["unknown", "stale", "recent"]


class OperatingIncomeReference(BaseModel):
    value: FiniteFloat
    source_field: Literal["annualTotalOperatingIncomeAsReported"]
    document_url: str
    document_location: str
    evidence_digest: str
    reviewed_at: datetime
    scope: str


class StatementPeriod(BaseModel):
    period_end: date
    period_type: Literal["annual"]
    currency: str | None
    source: Literal["yfinance"]
    unit: Literal["currency_units"]
    per_share_fields: list[str]
    values: dict[str, FiniteFloat | None]
    missing_fields: list[str]
    reported_operating_income_reference: OperatingIncomeReference | None = None


class Statements(BaseModel):
    income_statement: list[StatementPeriod]
    balance_sheet: list[StatementPeriod]
    cash_flow: list[StatementPeriod]


class FinancialSnapshot(BaseModel):
    schema_version: Literal["3.0", "3.1"]
    ticker: str
    display_ticker: str
    market: Literal["BR"]
    exchange: Literal["B3"]
    provider_used: Literal["yfinance"] | None
    retrieved_at: datetime
    quote: Quote | None
    statements: Statements
    fundamentals_available: bool
    common_period: date | None
    status: Literal["complete", "partial", "unavailable"]
    warnings: list[str]


class AnalysisError(BaseModel):
    code: str
    message: str


class MetricOperand(BaseModel):
    indicator: str
    statement: str
    value: FiniteFloat | None
    period_end: str | None
    currency: str | None
    source: str | None
    unit: str | None
    period_type: str | None


class CalculatedMetric(BaseModel):
    name: str
    period_end: str | None
    formula: str
    status: Literal["calculated", "unavailable"]
    value: FiniteFloat | None
    unit: str
    inputs: list[MetricOperand | None]
    reason: str | None
    note: str


class AnalysisResponse(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    ticker: str
    status: Literal["running", "completed", "failed"]
    stage: Literal["gathering", "quant", "cio", "done"]
    data: FinancialSnapshot | None
    interpretation_status: Literal["pending", "running", "completed", "failed", "skipped"]
    interpretation: str | None
    errors: list[AnalysisError]
    metrics: list[CalculatedMetric] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    storage: Literal["memory"] = "memory"
    max_concurrent: int
    max_records: int
    retention_seconds: int
