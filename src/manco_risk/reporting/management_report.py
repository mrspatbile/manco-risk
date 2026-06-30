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


class ManagementMarketRiskInput(BaseModel):
    """Input to management market risk summary builder.

    Contains already-computed market risk outputs required for the market risk section.

    Fields:
    - var_value: Value-at-Risk measure (Decimal, non-negative). Non-empty when supplied.
    - var_method: VaR calculation method (str, non-empty). E.g., "Historical Simulation", "Parametric".
    - expected_shortfall: Expected shortfall measure (Decimal, optional, non-negative when supplied).
    - srri_class: Synthetic Risk and Reward Indicator class (str, optional, non-empty when supplied).
      E.g., "1", "2", ..., "7".
    - global_exposure: Global exposure measure as ratio (Decimal, optional, non-negative when supplied).
    - stress_summary_reference: Reference to stress testing results (str, optional, non-empty when supplied).
    - methodology_version: Risk methodology version identifier (str, optional, non-empty when supplied).

    Invariants:
    - var_method must be non-empty.
    - var_value must be non-negative when supplied.
    - expected_shortfall must be non-negative when supplied.
    - global_exposure must be non-negative when supplied.
    - Optional string fields must be non-empty when supplied.

    Note: These are already-computed outputs from the risk module.
    This input model does not perform calculations.
    """

    var_value: Decimal
    var_method: str
    expected_shortfall: Optional[Decimal] = None
    srri_class: Optional[str] = None
    global_exposure: Optional[Decimal] = None
    stress_summary_reference: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("var_method")
    @classmethod
    def validate_var_method(cls, v: str) -> str:
        """VaR method must be non-empty."""
        if not v or not v.strip():
            raise ValueError("var_method must be non-empty")
        return v.strip()

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        if v < 0:
            raise ValueError("var_value must be non-negative")
        return v

    @field_validator("expected_shortfall")
    @classmethod
    def validate_expected_shortfall(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Expected shortfall must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("expected_shortfall must be non-negative")
        return v

    @field_validator("global_exposure")
    @classmethod
    def validate_global_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Global exposure must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("global_exposure must be non-negative")
        return v

    @field_validator("srri_class")
    @classmethod
    def validate_srri_class(cls, v: Optional[str]) -> Optional[str]:
        """SRRI class must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("srri_class must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("stress_summary_reference")
    @classmethod
    def validate_stress_summary_reference(cls, v: Optional[str]) -> Optional[str]:
        """Stress summary reference must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("stress_summary_reference must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: Optional[str]) -> Optional[str]:
        """Methodology version must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_version must be non-empty when supplied")
        return v.strip() if v else None


class ManagementMarketRiskSection(BaseModel):
    """Result of management market risk summary assembly.

    Immutable market risk section for management reporting.
    Contains already-computed market risk metrics.

    Fields:
    - var_value: Value-at-Risk measure.
    - var_method: VaR calculation method.
    - expected_shortfall: Expected shortfall measure (optional).
    - srri_class: Synthetic Risk and Reward Indicator class (optional).
    - global_exposure: Global exposure measure (optional).
    - stress_summary_reference: Reference to stress testing results (optional).
    - methodology_version: Risk methodology version (optional).

    Invariants (defensive checks):
    - var_method must be non-empty.
    - var_value must be non-negative.
    - expected_shortfall must be non-negative when present.
    - global_exposure must be non-negative when present.

    Note: These fields contain already-computed risk outputs.
    No calculations are performed by this model.
    """

    var_value: Decimal
    var_method: str
    expected_shortfall: Optional[Decimal] = None
    srri_class: Optional[str] = None
    global_exposure: Optional[Decimal] = None
    stress_summary_reference: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("var_method")
    @classmethod
    def validate_var_method(cls, v: str) -> str:
        """VaR method must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("var_method must be non-empty")
        return v

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError("var_value must be non-negative")
        return v

    @field_validator("expected_shortfall")
    @classmethod
    def validate_expected_shortfall(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Expected shortfall must be non-negative when present (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("expected_shortfall must be non-negative")
        return v

    @field_validator("global_exposure")
    @classmethod
    def validate_global_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Global exposure must be non-negative when present (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("global_exposure must be non-negative")
        return v


class ManagementRiskReport(BaseModel):
    """Management risk report container.

    Assembles management reporting sections into a consolidated report.
    For Slice 1, includes fund summary only.
    For Slice 2, optionally includes market risk.

    Fields:
    - fund_summary: Fund summary section (required).
    - market_risk: Market risk section (optional).
    - included_sections: List of section names included in the report.

    Invariants:
    - fund_summary must be present.
    - included_sections is computed from supplied sections.
    """

    fund_summary: ManagementFundSummarySection
    market_risk: Optional[ManagementMarketRiskSection] = None
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)
