"""Private equity analytics models.

Domain models for private equity investment analysis, including cash flows,
investment inputs, and computed multiples (DPI, RVPI, TVPI, MOIC).

No calculations performed in this module. Models are immutable Pydantic v2 with ConfigDict(frozen=True).
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

__all__ = [
    "PrivateEquityCashFlow",
    "PrivateEquityInvestmentInput",
    "PrivateEquityAnalyticsResult",
]


class PrivateEquityCashFlow(BaseModel):
    """Represents a single cash flow in a private equity investment.

    Attributes:
        flow_amount: Decimal, non-negative. Paid-in capital or distribution amount.
        flow_date: date, the date of the cash flow.
        flow_type: str, "paid_in" for contributions or "distribution" for distributions.
    """

    flow_amount: Decimal
    flow_date: date
    flow_type: str

    model_config = ConfigDict(frozen=True)

    @field_validator("flow_amount")
    @classmethod
    def validate_flow_amount(cls, v: Decimal) -> Decimal:
        """Flow amount must be non-negative."""
        if v < 0:
            raise ValueError("flow_amount must be non-negative")
        return v

    @field_validator("flow_type")
    @classmethod
    def validate_flow_type(cls, v: str) -> str:
        """Flow type must be 'paid_in' or 'distribution'."""
        normalized = v.lower()
        if normalized not in ("paid_in", "distribution"):
            raise ValueError("flow_type must be 'paid_in' or 'distribution'")
        return normalized


class PrivateEquityInvestmentInput(BaseModel):
    """Input model for private equity investment analysis.

    Receives a list of cash flows (contributions and distributions) and
    a residual value (remaining fund NAV or investment value).

    No calculations performed. Input validation only.

    Attributes:
        cash_flows: list[PrivateEquityCashFlow], may be empty.
        residual_value: Decimal, non-negative. Current NAV or remaining investment value.
        investment_id: str, optional. Investment identifier for reference.
    """

    cash_flows: list[PrivateEquityCashFlow]
    residual_value: Decimal
    investment_id: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("residual_value")
    @classmethod
    def validate_residual_value(cls, v: Decimal) -> Decimal:
        """Residual value must be non-negative."""
        if v < 0:
            raise ValueError("residual_value must be non-negative")
        return v


class PrivateEquityAnalyticsResult(BaseModel):
    """Immutable result model for private equity metrics.

    Contains computed multiples: DPI, RVPI, TVPI, MOIC.

    All ratios are stored as Decimal with positive values (e.g., 1.5 = 150%).

    Attributes:
        dpi: Decimal, Distributed to Paid-In ratio. None if no paid-in capital.
        rvpi: Decimal, Residual Value to Paid-In ratio. None if no paid-in capital.
        tvpi: Decimal, Total Value to Paid-In ratio. None if no paid-in capital.
        moic: Decimal, Multiple on Invested Capital (same as TVPI). None if no paid-in capital.
        total_paid_in: Decimal, sum of all paid-in capital.
        total_distributed: Decimal, sum of all distributions.
        residual_value: Decimal, current NAV or remaining investment value.
    """

    dpi: Optional[Decimal] = None
    rvpi: Optional[Decimal] = None
    tvpi: Optional[Decimal] = None
    moic: Optional[Decimal] = None
    total_paid_in: Decimal
    total_distributed: Decimal
    residual_value: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("dpi")
    @classmethod
    def validate_dpi(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """DPI must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("dpi must be non-negative")
        return v

    @field_validator("rvpi")
    @classmethod
    def validate_rvpi(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """RVPI must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("rvpi must be non-negative")
        return v

    @field_validator("tvpi")
    @classmethod
    def validate_tvpi(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """TVPI must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("tvpi must be non-negative")
        return v

    @field_validator("moic")
    @classmethod
    def validate_moic(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """MOIC must be non-negative."""
        if v is not None and v < 0:
            raise ValueError("moic must be non-negative")
        return v
