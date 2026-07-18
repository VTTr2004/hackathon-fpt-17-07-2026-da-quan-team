from datetime import date as Date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class CashDirection(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class CashActivity(StrEnum):
    OPERATING = "operating"
    INVESTING = "investing"
    FINANCING = "financing"
    UNCLASSIFIED = "unclassified"


class CashFlowTransaction(BaseModel):
    period: str
    date: Date | None = None
    direction: CashDirection
    activity: CashActivity = CashActivity.UNCLASSIFIED
    category: str = "unclassified"
    amount: Decimal
    description: str | None = None
    source_ref: str | None = None
    document_id: str | None = None
    filename: str | None = None
    sheet: str | None = None
    row_number: int | None = None
    evidence_id: str | None = None
    is_recurring: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value < 0:
            raise ValueError("amount must be a finite non-negative number")
        return value


class CashFlowDataset(BaseModel):
    currency: str = "VND"
    opening_cash: Decimal | None = None
    reported_ending_cash: Decimal | None = None
    cash_as_of: Date | None = None
    transactions: list[CashFlowTransaction] = Field(default_factory=list)
    source_type: str = "structured_facts"
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class CashFlowPeriodSummary(BaseModel):
    period: str
    operating_inflow: Decimal = Decimal(0)
    operating_outflow: Decimal = Decimal(0)
    net_operating_cash_flow: Decimal = Decimal(0)
    investing_inflow: Decimal = Decimal(0)
    investing_outflow: Decimal = Decimal(0)
    net_investing_cash_flow: Decimal = Decimal(0)
    financing_inflow: Decimal = Decimal(0)
    financing_outflow: Decimal = Decimal(0)
    net_financing_cash_flow: Decimal = Decimal(0)
    net_cash_flow: Decimal = Decimal(0)
    ending_cash: Decimal | None = None
