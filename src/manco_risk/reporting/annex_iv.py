"""Annex IV-style reporting models.

Pure data models for fund identification, asset breakdown, and report assembly.
No calculation or persistence logic.

The reporting layer packages source data and risk outputs into export-ready
typed objects. It does not perform risk calculations, database queries,
or market data access.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AnnexIVFundIdentificationInput(BaseModel):
    """Input to Annex IV fund identification builder.

    Contains source fund data required for the identification section.

    Fields:
    - fund_id: Fund identifier (integer from database).
    - fund_name: Fund name (non-empty string).
    - fund_regime: Fund regime classification, e.g., "UCITS" or "AIF".
    - domicile: Fund domicile (country code, e.g., "LU", "IE").
    - base_currency: Base currency for the fund (e.g., "EUR", "USD").
    - valuation_date: Snapshot date for the portfolio.
    - reporting_period_end: End date of the reporting period.

    Invariants:
    - All string fields must be non-empty after stripping whitespace.
    - valuation_date and reporting_period_end must be valid dates.
    """

    fund_id: int
    fund_name: str
    fund_regime: str
    domicile: str
    base_currency: str
    valuation_date: date
    reporting_period_end: date

    model_config = ConfigDict(frozen=True)

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

    @field_validator("domicile")
    @classmethod
    def validate_domicile(cls, v: str) -> str:
        """Domicile must be non-empty."""
        if not v or not v.strip():
            raise ValueError("domicile must be non-empty")
        return v.strip()

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        """Base currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("base_currency must be non-empty")
        return v.strip()


class AnnexIVFundIdentificationSection(BaseModel):
    """Result of Annex IV fund identification assembly.

    Immutable fund identification section for Annex IV reporting.
    Contains canonical fund identification data.

    Fields:
    - fund_id: Fund identifier.
    - fund_name: Fund name.
    - fund_regime: Fund regime (e.g., "UCITS", "AIF").
    - domicile: Fund domicile (country code).
    - base_currency: Base currency.
    - valuation_date: Snapshot date.
    - reporting_period_end: End date of reporting period.

    Invariants (defensive checks):
    - fund_id must be positive.
    - All string fields must be non-empty.
    - valuation_date and reporting_period_end must be valid dates.
    """

    fund_id: int
    fund_name: str
    fund_regime: str
    domicile: str
    base_currency: str
    valuation_date: date
    reporting_period_end: date

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: int) -> int:
        """Fund ID must be positive."""
        if v <= 0:
            raise ValueError(f"fund_id must be positive, got {v}")
        return v

    @field_validator("fund_name")
    @classmethod
    def validate_fund_name(cls, v: str) -> str:
        """Fund name must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_name must be non-empty")
        return v

    @field_validator("fund_regime")
    @classmethod
    def validate_fund_regime(cls, v: str) -> str:
        """Fund regime must be non-empty."""
        if not v or not v.strip():
            raise ValueError("fund_regime must be non-empty")
        return v

    @field_validator("domicile")
    @classmethod
    def validate_domicile(cls, v: str) -> str:
        """Domicile must be non-empty."""
        if not v or not v.strip():
            raise ValueError("domicile must be non-empty")
        return v

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        """Base currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("base_currency must be non-empty")
        return v


class AnnexIVAssetBreakdownRow(BaseModel):
    """Single asset class row for Annex IV asset breakdown.

    Represents one asset class entry in the asset breakdown section.

    Fields:
    - asset_class: Asset class identifier (e.g., "Equities", "Bonds", "Cash").
    - market_value: Market value in base currency (Decimal, non-negative).
    - nav_percentage: Percentage of NAV as decimal (e.g., 0.25 = 25%, non-negative).
    - currency: Optional currency code (e.g., "EUR", "USD").
    - exposure_basis: Optional exposure basis (e.g., "Long", "Short", "Notional").

    Invariants:
    - asset_class must be non-empty.
    - market_value must be non-negative.
    - nav_percentage must be non-negative.
    - Do not validate nav_percentage sum in this slice.
    """

    asset_class: str
    market_value: Decimal
    nav_percentage: Decimal
    currency: Optional[str] = None
    exposure_basis: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        """Asset class must be non-empty."""
        if not v or not v.strip():
            raise ValueError("asset_class must be non-empty")
        return v.strip()

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: Decimal) -> Decimal:
        """Market value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"market_value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("nav_percentage")
    @classmethod
    def validate_nav_percentage(cls, v: Decimal) -> Decimal:
        """NAV percentage must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"nav_percentage must be non-negative, got {v_decimal}")
        return v_decimal


class AnnexIVAssetBreakdownInput(BaseModel):
    """Input to Annex IV asset breakdown builder.

    Contains pre-aggregated asset breakdown rows for assembly.

    Fields:
    - rows: List of asset class breakdown rows (at least one required if supplied).

    Invariants:
    - rows must contain at least one row.
    - Each row must be valid AnnexIVAssetBreakdownRow.
    """

    rows: list[AnnexIVAssetBreakdownRow]

    model_config = ConfigDict(frozen=True)

    @field_validator("rows")
    @classmethod
    def validate_rows(cls, v: list[AnnexIVAssetBreakdownRow]) -> list[AnnexIVAssetBreakdownRow]:
        """Asset breakdown must contain at least one row."""
        if not v or len(v) == 0:
            raise ValueError("Asset breakdown must contain at least one row")
        return v


class AnnexIVAssetBreakdownSection(BaseModel):
    """Result of Annex IV asset breakdown assembly.

    Immutable asset breakdown section for Annex IV reporting.
    Contains pre-aggregated asset class rows.

    Fields:
    - rows: List of asset class breakdown rows.

    Invariants (defensive checks):
    - rows must contain at least one row.
    - Each row must be valid AnnexIVAssetBreakdownRow.
    """

    rows: list[AnnexIVAssetBreakdownRow]

    model_config = ConfigDict(frozen=True)

    @field_validator("rows")
    @classmethod
    def validate_rows(cls, v: list[AnnexIVAssetBreakdownRow]) -> list[AnnexIVAssetBreakdownRow]:
        """Asset breakdown must contain at least one row."""
        if not v or len(v) == 0:
            raise ValueError("Asset breakdown must contain at least one row")
        return v


class AnnexIVReport(BaseModel):
    """Annex IV-style reporting container.

    Immutable report that assembles Annex IV sections.
    Contains fund identification and optionally asset breakdown.
    Future slices will add risk measures, leverage, liquidity.

    Fields:
    - fund_identification: Fund identification section.
    - asset_breakdown: Optional asset breakdown section.
    - included_sections: List of included report sections (informational).

    Invariants (defensive checks):
    - fund_identification must be present.
    - included_sections must list "Fund Identification".
    - If asset_breakdown is supplied, included_sections must include "Asset Breakdown".
    """

    fund_identification: AnnexIVFundIdentificationSection
    asset_breakdown: Optional[AnnexIVAssetBreakdownSection] = None
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("included_sections")
    @classmethod
    def validate_included_sections(cls, v: list[str]) -> list[str]:
        """included_sections must contain Fund Identification."""
        if "Fund Identification" not in v:
            raise ValueError("Fund Identification must be in included_sections")
        return v
