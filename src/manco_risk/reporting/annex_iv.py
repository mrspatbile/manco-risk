"""Annex IV-style reporting models.

Pure data models for fund identification and report assembly.
No calculation or persistence logic.

The reporting layer packages source data and risk outputs into export-ready
typed objects. It does not perform risk calculations, database queries,
or market data access.
"""

from datetime import date

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


class AnnexIVReport(BaseModel):
    """Annex IV-style reporting container.

    Immutable report that assembles Annex IV sections.
    For this slice, contains fund identification only.
    Future slices will add asset breakdown, risk measures, leverage, liquidity.

    Fields:
    - fund_identification: Fund identification section.
    - included_sections: List of included report sections (informational).

    Invariants (defensive checks):
    - fund_identification must be present.
    - included_sections must list "Fund Identification".
    """

    fund_identification: AnnexIVFundIdentificationSection
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("included_sections")
    @classmethod
    def validate_included_sections(cls, v: list[str]) -> list[str]:
        """included_sections must contain Fund Identification."""
        if "Fund Identification" not in v:
            raise ValueError("Fund Identification must be in included_sections")
        return v
