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


class ManagementStressTestingInput(BaseModel):
    """Input to management stress testing summary builder.

    Contains already-computed stress testing outputs required for the stress testing section.

    Fields:
    - scenario_name: Name of the stress scenario (str, non-empty).
      E.g., "Lehman Crisis 2008", "COVID-19 March 2020", "Rates +100bps".
    - scenario_type: Type of stress scenario (str, non-empty).
      E.g., "Historical", "Hypothetical", "Reverse Stress".
    - portfolio_impact: Portfolio P&L impact under stress (Decimal). Can be negative (loss).
    - nav_impact: NAV impact under stress (Decimal, optional). Can be negative.
    - worst_position: Worst performing position identifier (str, optional, non-empty when supplied).
    - worst_sector: Worst performing sector (str, optional, non-empty when supplied).
    - stress_date: Date of the stress scenario (date, optional).
    - methodology_version: Stress testing methodology version (str, optional, non-empty when supplied).

    Invariants:
    - scenario_name and scenario_type must be non-empty.
    - Decimal values can be positive or negative (losses/gains).
    - Optional string fields must be non-empty when supplied.

    Note: These are already-computed outputs from the risk module.
    This input model does not perform stress calculations.
    """

    scenario_name: str
    scenario_type: str
    portfolio_impact: Decimal
    nav_impact: Optional[Decimal] = None
    worst_position: Optional[str] = None
    worst_sector: Optional[str] = None
    stress_date: Optional[date] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("scenario_name")
    @classmethod
    def validate_scenario_name(cls, v: str) -> str:
        """Scenario name must be non-empty."""
        if not v or not v.strip():
            raise ValueError("scenario_name must be non-empty")
        return v.strip()

    @field_validator("scenario_type")
    @classmethod
    def validate_scenario_type(cls, v: str) -> str:
        """Scenario type must be non-empty."""
        if not v or not v.strip():
            raise ValueError("scenario_type must be non-empty")
        return v.strip()

    @field_validator("worst_position")
    @classmethod
    def validate_worst_position(cls, v: Optional[str]) -> Optional[str]:
        """Worst position must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("worst_position must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("worst_sector")
    @classmethod
    def validate_worst_sector(cls, v: Optional[str]) -> Optional[str]:
        """Worst sector must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("worst_sector must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: Optional[str]) -> Optional[str]:
        """Methodology version must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_version must be non-empty when supplied")
        return v.strip() if v else None


class ManagementStressTestingSection(BaseModel):
    """Result of management stress testing summary assembly.

    Immutable stress testing section for management reporting.
    Contains already-computed stress test scenario outcomes.

    Fields:
    - scenario_name: Name of the stress scenario.
    - scenario_type: Type of scenario (Historical, Hypothetical, Reverse Stress).
    - portfolio_impact: Portfolio P&L impact (can be negative).
    - nav_impact: NAV impact (optional, can be negative).
    - worst_position: Worst performing position (optional).
    - worst_sector: Worst performing sector (optional).
    - stress_date: Date of scenario (optional).
    - methodology_version: Stress testing methodology version (optional).

    Invariants (defensive checks):
    - scenario_name and scenario_type must be non-empty.
    - Decimal values can be positive or negative.

    Note: These fields contain already-computed stress test outputs.
    No calculations are performed by this model.
    """

    scenario_name: str
    scenario_type: str
    portfolio_impact: Decimal
    nav_impact: Optional[Decimal] = None
    worst_position: Optional[str] = None
    worst_sector: Optional[str] = None
    stress_date: Optional[date] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("scenario_name")
    @classmethod
    def validate_scenario_name(cls, v: str) -> str:
        """Scenario name must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("scenario_name must be non-empty")
        return v

    @field_validator("scenario_type")
    @classmethod
    def validate_scenario_type(cls, v: str) -> str:
        """Scenario type must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("scenario_type must be non-empty")
        return v


class ManagementLiquidityInput(BaseModel):
    """Input to management liquidity summary builder.

    Contains already-computed liquidity outputs required for the liquidity section.

    Fields:
    - liquidity_ratio: Liquidity ratio (Decimal, required, non-negative).
      Range 0–1. Example: `0.75` = 75% liquid assets.
    - liquid_assets: Amount of liquid assets (Decimal, required, non-negative).
      In base currency.
    - illiquid_assets: Amount of illiquid assets (Decimal, required, non-negative).
      In base currency.
    - average_time_to_liquidate_days: Average time to liquidate portfolio (int, optional, non-negative).
      In days.
    - redemption_profile: Redemption frequency (str, optional, non-empty when supplied).
      Examples: "Daily", "Weekly", "Monthly", "Quarterly".
    - liquidity_bucket_summary: Summary of liquidity bucket distribution (str, optional, non-empty).
      E.g., "65% 0-1d, 20% 1-7d, 15% >7d".
    - active_lmts: Number of active liquidity management tools (int, optional, non-negative).
    - liquidity_warning: Liquidity warning message if applicable (str, optional, non-empty).
      E.g., "Position concentration in illiquid securities".
    - methodology_version: Liquidity methodology version (str, optional, non-empty when supplied).

    Invariants:
    - liquidity_ratio, liquid_assets, illiquid_assets must be non-negative.
    - average_time_to_liquidate_days and active_lmts must be non-negative when supplied.
    - Optional string fields must be non-empty when supplied.

    Note: These are already-computed outputs from the risk module.
    This input model does not perform liquidity calculations.
    """

    liquidity_ratio: Decimal
    liquid_assets: Decimal
    illiquid_assets: Decimal
    average_time_to_liquidate_days: Optional[int] = None
    redemption_profile: Optional[str] = None
    liquidity_bucket_summary: Optional[str] = None
    active_lmts: Optional[int] = None
    liquidity_warning: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("liquidity_ratio")
    @classmethod
    def validate_liquidity_ratio(cls, v: Decimal) -> Decimal:
        """Liquidity ratio must be non-negative."""
        if v < 0:
            raise ValueError("liquidity_ratio must be non-negative")
        return v

    @field_validator("liquid_assets")
    @classmethod
    def validate_liquid_assets(cls, v: Decimal) -> Decimal:
        """Liquid assets must be non-negative."""
        if v < 0:
            raise ValueError("liquid_assets must be non-negative")
        return v

    @field_validator("illiquid_assets")
    @classmethod
    def validate_illiquid_assets(cls, v: Decimal) -> Decimal:
        """Illiquid assets must be non-negative."""
        if v < 0:
            raise ValueError("illiquid_assets must be non-negative")
        return v

    @field_validator("average_time_to_liquidate_days")
    @classmethod
    def validate_average_time_to_liquidate_days(cls, v: Optional[int]) -> Optional[int]:
        """Average time to liquidate days must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("average_time_to_liquidate_days must be non-negative")
        return v

    @field_validator("active_lmts")
    @classmethod
    def validate_active_lmts(cls, v: Optional[int]) -> Optional[int]:
        """Active LMTs must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("active_lmts must be non-negative")
        return v

    @field_validator("redemption_profile")
    @classmethod
    def validate_redemption_profile(cls, v: Optional[str]) -> Optional[str]:
        """Redemption profile must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("redemption_profile must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("liquidity_bucket_summary")
    @classmethod
    def validate_liquidity_bucket_summary(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity bucket summary must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("liquidity_bucket_summary must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("liquidity_warning")
    @classmethod
    def validate_liquidity_warning(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity warning must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("liquidity_warning must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: Optional[str]) -> Optional[str]:
        """Methodology version must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_version must be non-empty when supplied")
        return v.strip() if v else None


class ManagementLiquiditySection(BaseModel):
    """Result of management liquidity summary assembly.

    Immutable liquidity section for management reporting.
    Contains already-computed liquidity metrics.

    Fields:
    - liquidity_ratio: Liquidity ratio (0–1 range).
    - liquid_assets: Amount of liquid assets in base currency.
    - illiquid_assets: Amount of illiquid assets in base currency.
    - average_time_to_liquidate_days: Average time to liquidate (optional, in days).
    - redemption_profile: Redemption frequency (optional).
    - liquidity_bucket_summary: Bucket distribution summary (optional).
    - active_lmts: Number of active liquidity management tools (optional).
    - liquidity_warning: Liquidity warning message (optional).
    - methodology_version: Liquidity methodology version (optional).

    Invariants (defensive checks):
    - liquidity_ratio, liquid_assets, illiquid_assets must be non-negative.
    - average_time_to_liquidate_days and active_lmts must be non-negative when present.

    Note: These fields contain already-computed liquidity outputs.
    No calculations are performed by this model.
    """

    liquidity_ratio: Decimal
    liquid_assets: Decimal
    illiquid_assets: Decimal
    average_time_to_liquidate_days: Optional[int] = None
    redemption_profile: Optional[str] = None
    liquidity_bucket_summary: Optional[str] = None
    active_lmts: Optional[int] = None
    liquidity_warning: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("liquidity_ratio")
    @classmethod
    def validate_liquidity_ratio(cls, v: Decimal) -> Decimal:
        """Liquidity ratio must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError("liquidity_ratio must be non-negative")
        return v

    @field_validator("liquid_assets")
    @classmethod
    def validate_liquid_assets(cls, v: Decimal) -> Decimal:
        """Liquid assets must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError("liquid_assets must be non-negative")
        return v

    @field_validator("illiquid_assets")
    @classmethod
    def validate_illiquid_assets(cls, v: Decimal) -> Decimal:
        """Illiquid assets must be non-negative (defensive check)."""
        if v < 0:
            raise ValueError("illiquid_assets must be non-negative")
        return v

    @field_validator("average_time_to_liquidate_days")
    @classmethod
    def validate_average_time_to_liquidate_days(cls, v: Optional[int]) -> Optional[int]:
        """Average time to liquidate days must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("average_time_to_liquidate_days must be non-negative")
        return v

    @field_validator("active_lmts")
    @classmethod
    def validate_active_lmts(cls, v: Optional[int]) -> Optional[int]:
        """Active LMTs must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("active_lmts must be non-negative")
        return v


class ManagementLeverageInput(BaseModel):
    """Input to management leverage summary builder.

    Contains already-computed leverage outputs required for the leverage section.

    Fields:
    - gross_leverage_ratio: Gross leverage ratio (Decimal, optional, non-negative).
      Range typically 0+. Example: `2.5` = 250% gross leverage.
    - commitment_leverage_ratio: Commitment leverage ratio (Decimal, optional, non-negative).
      Range typically 0+. Example: `2.0` = 200% commitment leverage.
    - gross_exposure: Gross exposure amount (Decimal, optional, non-negative).
      In base currency.
    - commitment_exposure: Commitment exposure amount (Decimal, optional, non-negative).
      In base currency.
    - nav: Net asset value (Decimal, optional, non-negative).
      In base currency. May duplicate fund summary data.
    - leverage_limit: Maximum allowed leverage ratio (Decimal, optional, non-negative).
      Example: `3.0` = 300% maximum leverage.
    - leverage_warning: Leverage warning message if applicable (str, optional, non-empty).
      E.g., "Approaching leverage limit", "Excess concentration".
    - methodology_version: Leverage methodology version (str, optional, non-empty when supplied).

    Invariants:
    - Ratios and monetary values must be non-negative when supplied.
    - Not both gross_leverage_ratio and commitment_leverage_ratio must be present (either is ok).
    - Optional string fields must be non-empty when supplied.

    Note: These are already-computed outputs from the risk module.
    This input model does not perform leverage calculations.
    """

    gross_leverage_ratio: Optional[Decimal] = None
    commitment_leverage_ratio: Optional[Decimal] = None
    gross_exposure: Optional[Decimal] = None
    commitment_exposure: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    leverage_limit: Optional[Decimal] = None
    leverage_warning: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("gross_leverage_ratio")
    @classmethod
    def validate_gross_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross leverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("gross_leverage_ratio must be non-negative")
        return v

    @field_validator("commitment_leverage_ratio")
    @classmethod
    def validate_commitment_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment leverage ratio must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("commitment_leverage_ratio must be non-negative")
        return v

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross exposure must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("gross_exposure must be non-negative")
        return v

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment exposure must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("commitment_exposure must be non-negative")
        return v

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """NAV must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("nav must be non-negative")
        return v

    @field_validator("leverage_limit")
    @classmethod
    def validate_leverage_limit(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Leverage limit must be non-negative when supplied."""
        if v is not None and v < 0:
            raise ValueError("leverage_limit must be non-negative")
        return v

    @field_validator("leverage_warning")
    @classmethod
    def validate_leverage_warning(cls, v: Optional[str]) -> Optional[str]:
        """Leverage warning must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("leverage_warning must be non-empty when supplied")
        return v.strip() if v else None

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: Optional[str]) -> Optional[str]:
        """Methodology version must be non-empty when supplied."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("methodology_version must be non-empty when supplied")
        return v.strip() if v else None


class ManagementLeverageSection(BaseModel):
    """Result of management leverage summary assembly.

    Immutable leverage section for management reporting.
    Contains already-computed leverage metrics.

    Fields:
    - gross_leverage_ratio: Gross leverage ratio (optional).
    - commitment_leverage_ratio: Commitment leverage ratio (optional).
    - gross_exposure: Gross exposure amount (optional).
    - commitment_exposure: Commitment exposure amount (optional).
    - nav: Net asset value (optional).
    - leverage_limit: Maximum allowed leverage ratio (optional).
    - leverage_warning: Leverage warning message (optional).
    - methodology_version: Leverage methodology version (optional).

    Invariants (defensive checks):
    - Ratios and monetary values must be non-negative when present.

    Note: These fields contain already-computed leverage outputs.
    No calculations are performed by this model.
    """

    gross_leverage_ratio: Optional[Decimal] = None
    commitment_leverage_ratio: Optional[Decimal] = None
    gross_exposure: Optional[Decimal] = None
    commitment_exposure: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    leverage_limit: Optional[Decimal] = None
    leverage_warning: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("gross_leverage_ratio")
    @classmethod
    def validate_gross_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross leverage ratio must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("gross_leverage_ratio must be non-negative")
        return v

    @field_validator("commitment_leverage_ratio")
    @classmethod
    def validate_commitment_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment leverage ratio must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("commitment_leverage_ratio must be non-negative")
        return v

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross exposure must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("gross_exposure must be non-negative")
        return v

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment exposure must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("commitment_exposure must be non-negative")
        return v

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """NAV must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("nav must be non-negative")
        return v

    @field_validator("leverage_limit")
    @classmethod
    def validate_leverage_limit(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Leverage limit must be non-negative (defensive check)."""
        if v is not None and v < 0:
            raise ValueError("leverage_limit must be non-negative")
        return v


class ManagementRiskReport(BaseModel):
    """Management risk report container.

    Assembles management reporting sections into a consolidated report.
    For Slice 1, includes fund summary only.
    For Slice 2, optionally includes market risk.
    For Slice 3, optionally includes stress testing.
    For Slice 4, optionally includes liquidity.
    For Slice 5, optionally includes leverage.

    Fields:
    - fund_summary: Fund summary section (required).
    - market_risk: Market risk section (optional).
    - stress_testing: Stress testing section (optional).
    - liquidity: Liquidity section (optional).
    - leverage: Leverage section (optional).
    - included_sections: List of section names included in the report.

    Invariants:
    - fund_summary must be present.
    - included_sections is computed from supplied sections.
    """

    fund_summary: ManagementFundSummarySection
    market_risk: Optional[ManagementMarketRiskSection] = None
    stress_testing: Optional[ManagementStressTestingSection] = None
    liquidity: Optional[ManagementLiquiditySection] = None
    leverage: Optional[ManagementLeverageSection] = None
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)
