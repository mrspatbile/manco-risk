"""Management reporting models for fund review and governance.

Pure data models for fund summary and management risk reporting.
No calculation, persistence, or display-specific logic.

The management reporting layer packages source data and already-computed risk
outputs into export-ready typed objects. It does not perform risk calculations,
query databases, fetch market data, or contain visualization code.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ManagementFundSummaryInput(BaseModel):
    """Input to management fund summary builder.

    Contains source fund data required for the fund summary section.

    Fields:
    - fund_id: Fund identifier (string, non-empty).
    - fund_name: Fund name (non-empty string).
    - fund_regime: Fund regime classification, e.g., "UCITS" or "AIF".
    - base_currency: Base currency for the fund (e.g., "EUR", "USD").
    - valuation_date: Snapshot date for the portfolio.
    - nav: Net asset value in base_currency. Must be non-negative.
    - aum: Assets under management (optional). Must be non-negative when supplied.
    - inception_date: Fund inception date (optional).
    - reporting_period_end: End date of the reporting period (optional).
    - methodology_version: Risk methodology version identifier (optional).

    Invariants:
    - fund_id, fund_name, fund_regime, base_currency must be non-empty.
    - nav must be non-negative.
    - aum must be non-negative when supplied.
    - Optional string fields must be non-empty when supplied.
    """

    fund_id: str
    fund_name: str
    fund_regime: str
    base_currency: str
    valuation_date: date
    nav: Decimal
    aum: Optional[Decimal] = None
    inception_date: Optional[date] = None
    reporting_period_end: Optional[date] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v.strip()

    @field_validator("fund_name")
    @classmethod
    def validate_fund_name(cls, v: str) -> str:
        """Fund name must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_name must be non-empty")
        return v.strip()

    @field_validator("fund_regime")
    @classmethod
    def validate_fund_regime(cls, v: str) -> str:
        """Fund regime must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_regime must be non-empty")
        return v.strip()

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        """Base currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("base_currency must be non-empty")
        return v.strip()

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be non-negative."""
        if v < 0:
            raise ValueError("nav must be non-negative")
        return v

    @field_validator("aum")
    @classmethod
    def validate_aum(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """AUM must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("aum must be non-negative")
        return v

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: Optional[str]) -> Optional[str]:
        """Methodology version must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_version must be non-empty when supplied")
        return v.strip() if v else None


class ManagementFundSummarySection(BaseModel):
    """Result of management fund summary assembly.

    Immutable fund summary section for management reporting.
    Contains canonical fund identification and key metrics data.

    Fields:
    - fund_id: Fund identifier.
    - fund_name: Fund name.
    - fund_regime: Fund regime (e.g., "UCITS", "AIF").
    - base_currency: Base currency.
    - valuation_date: Snapshot date.
    - nav: Net asset value in base_currency.
    - aum: Assets under management (optional).
    - inception_date: Fund inception date (optional).
    - reporting_period_end: End date of reporting period (optional).
    - methodology_version: Risk methodology version (optional).

    Invariants (defensive checks):
    - All string fields must be non-empty.
    - nav must be non-negative.
    - aum must be non-negative when supplied.
    """

    fund_id: str
    fund_name: str
    fund_regime: str
    base_currency: str
    valuation_date: date
    nav: Decimal
    aum: Optional[Decimal] = None
    inception_date: Optional[date] = None
    reporting_period_end: Optional[date] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: str) -> str:
        """Fund ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("fund_id must be non-empty")
        return v

    @field_validator("fund_name")
    @classmethod
    def validate_fund_name(cls, v: str) -> str:
        """Fund name must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("fund_name must be non-empty")
        return v

    @field_validator("fund_regime")
    @classmethod
    def validate_fund_regime(cls, v: str) -> str:
        """Fund regime must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("fund_regime must be non-empty")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        """Base currency must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("base_currency must be non-empty")
        return v

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError("nav must be non-negative")
        return v

    @field_validator("aum")
    @classmethod
    def validate_aum(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """AUM must be non-negative when present (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("aum must be non-negative")
        return v


class ManagementRiskReport(BaseModel):
    """Management risk report container.

    Assembles management reporting sections into a consolidated report.
    For Slice 1, only fund summary is included.

    Fields:
    - fund_summary: Fund summary section (required).
    - included_sections: List of section names included in the report.

    Invariants:
    - fund_summary must be present (fund summary is mandatory for Slice 1).
    - included_sections is computed from supplied sections.
    """

    fund_summary: ManagementFundSummarySection
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)
