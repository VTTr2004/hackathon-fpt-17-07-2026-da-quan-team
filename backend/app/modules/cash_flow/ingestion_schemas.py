from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.cash_flow.schemas import CashFlowDataset
from app.schemas.common import Evidence, ToolCall


class IngestionToolName(StrEnum):
    NORMALIZE_CASHBOOK = "normalize_cashbook"
    EXTRACT_FINANCIAL_FACTS = "extract_financial_facts"
    SUMMARIZE_SALES = "summarize_sales"
    SUMMARIZE_PURCHASES = "summarize_purchases"


class SheetRowSample(BaseModel):
    row_number: int = Field(ge=1)
    values: list[Any]


class WorkbookSheetProfile(BaseModel):
    document_id: str
    filename: str
    sheet: str
    max_row: int = Field(ge=0)
    max_column: int = Field(ge=0)
    sampled_rows: list[SheetRowSample] = Field(default_factory=list)


class IngestionToolRequest(BaseModel):
    tool: IngestionToolName
    document_id: str
    sheet: str
    header_row: int = Field(ge=1)
    columns: dict[str, int] = Field(default_factory=dict)
    field_map: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None

    @field_validator("columns")
    @classmethod
    def column_indexes_are_one_based(cls, value: dict[str, int]) -> dict[str, int]:
        if any(isinstance(index, bool) or index < 1 for index in value.values()):
            raise ValueError("column indexes must be one-based positive integers")
        return value


class CashFlowIngestionPlan(BaseModel):
    calls: list[IngestionToolRequest] = Field(default_factory=list, max_length=24)
    ignored_sheets: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ProposalSource(BaseModel):
    document_id: str
    filename: str
    sheet: str
    range: str | None = None


class FieldProposal(BaseModel):
    proposal_id: str = ""
    field: str
    value: Any
    status: str = "proposed"
    confidence: str = "medium"
    sources: list[ProposalSource] = Field(default_factory=list)
    generated_by_tool: str
    warnings: list[str] = Field(default_factory=list)


class ToolExecutionResult(BaseModel):
    dataset: CashFlowDataset | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    proposals: list[FieldProposal] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CashFlowIngestionResult(BaseModel):
    preview_id: str = ""
    plan_source: str
    plan: CashFlowIngestionPlan
    dataset: CashFlowDataset | None = None
    supporting_metrics: dict[str, Any] = Field(default_factory=dict)
    proposals: list[FieldProposal] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkingCapitalInput(BaseModel):
    accounts_receivable: Decimal = Decimal(0)
    accounts_payable: Decimal = Decimal(0)
    inventory: Decimal = Decimal(0)
    period_revenue: Decimal | None = None
    period_cogs: Decimal | None = None
    period_days: int | None = Field(default=None, ge=1, le=366)

    @field_validator("accounts_receivable", "accounts_payable", "inventory")
    @classmethod
    def balances_are_finite_and_non_negative(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value < 0:
            raise ValueError("working-capital balances must be finite and non-negative")
        return value
