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


class AnnexIVRiskMeasuresInput(BaseModel):
    """Input to Annex IV risk measures builder.

    Contains already-computed risk measure values.
    The reporting layer does NOT calculate risk measures.

    Fields:
    - var_value: Value-at-Risk loss threshold (Decimal, non-negative).
    - var_method: VaR calculation method (e.g., "Historical", "Parametric", "Student-t").
    - var_confidence_level: Confidence level for VaR (Decimal, e.g., 0.95).
    - var_horizon_days: Horizon in days for VaR (int, typically 1).
    - expected_shortfall: Expected Shortfall loss threshold (Decimal, non-negative, optional).
    - es_confidence_level: Confidence level for ES (Decimal, optional).
    - stress_test_reference: Reference to stress test scenario (str, optional).
    - global_exposure: Global exposure measure (Decimal, optional).
    - methodology_version: Version of risk methodology (str, optional).

    Invariants:
    - var_value must be non-negative.
    - var_method must be non-empty.
    - var_confidence_level must be non-negative decimal.
    - var_horizon_days must be positive.
    - expected_shortfall (if supplied) must be non-negative.
    - es_confidence_level (if supplied) must be non-negative decimal.
    - global_exposure (if supplied) must be non-negative.
    """

    var_value: Decimal
    var_method: str
    var_confidence_level: Decimal
    var_horizon_days: int
    expected_shortfall: Optional[Decimal] = None
    es_confidence_level: Optional[Decimal] = None
    stress_test_reference: Optional[str] = None
    global_exposure: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"var_value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("var_method")
    @classmethod
    def validate_var_method(cls, v: str) -> str:
        """VaR method must be non-empty."""
        if not v or not v.strip():
            raise ValueError("var_method must be non-empty")
        return v.strip()

    @field_validator("var_confidence_level")
    @classmethod
    def validate_var_confidence_level(cls, v: Decimal) -> Decimal:
        """VaR confidence level must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"var_confidence_level must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("var_horizon_days")
    @classmethod
    def validate_var_horizon_days(cls, v: int) -> int:
        """VaR horizon must be positive."""
        if v <= 0:
            raise ValueError(f"var_horizon_days must be positive, got {v}")
        return v

    @field_validator("expected_shortfall")
    @classmethod
    def validate_expected_shortfall(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Expected Shortfall must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"expected_shortfall must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("es_confidence_level")
    @classmethod
    def validate_es_confidence_level(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """ES confidence level must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"es_confidence_level must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("global_exposure")
    @classmethod
    def validate_global_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Global exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"global_exposure must be non-negative, got {v_decimal}")
        return v_decimal


class AnnexIVRiskMeasuresSection(BaseModel):
    """Result of Annex IV risk measures assembly.

    Immutable risk measures section for Annex IV reporting.
    Contains already-computed risk measure values.

    Fields:
    - var_value: Value-at-Risk loss threshold (Decimal).
    - var_method: VaR calculation method.
    - var_confidence_level: Confidence level for VaR (Decimal).
    - var_horizon_days: Horizon in days for VaR (int).
    - expected_shortfall: Expected Shortfall loss threshold (Decimal, optional).
    - es_confidence_level: Confidence level for ES (Decimal, optional).
    - stress_test_reference: Reference to stress test scenario (str, optional).
    - global_exposure: Global exposure measure (Decimal, optional).
    - methodology_version: Version of risk methodology (str, optional).

    Invariants (defensive checks):
    - var_value must be non-negative.
    - var_method must be non-empty.
    - var_confidence_level must be non-negative.
    - var_horizon_days must be positive.
    - expected_shortfall (if supplied) must be non-negative.
    - es_confidence_level (if supplied) must be non-negative.
    - global_exposure (if supplied) must be non-negative.
    """

    var_value: Decimal
    var_method: str
    var_confidence_level: Decimal
    var_horizon_days: int
    expected_shortfall: Optional[Decimal] = None
    es_confidence_level: Optional[Decimal] = None
    stress_test_reference: Optional[str] = None
    global_exposure: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"var_value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("var_method")
    @classmethod
    def validate_var_method(cls, v: str) -> str:
        """VaR method must be non-empty."""
        if not v or not v.strip():
            raise ValueError("var_method must be non-empty")
        return v

    @field_validator("var_confidence_level")
    @classmethod
    def validate_var_confidence_level(cls, v: Decimal) -> Decimal:
        """VaR confidence level must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"var_confidence_level must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("var_horizon_days")
    @classmethod
    def validate_var_horizon_days(cls, v: int) -> int:
        """VaR horizon must be positive."""
        if v <= 0:
            raise ValueError(f"var_horizon_days must be positive, got {v}")
        return v

    @field_validator("expected_shortfall")
    @classmethod
    def validate_expected_shortfall(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Expected Shortfall must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"expected_shortfall must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("es_confidence_level")
    @classmethod
    def validate_es_confidence_level(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """ES confidence level must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"es_confidence_level must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("global_exposure")
    @classmethod
    def validate_global_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Global exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"global_exposure must be non-negative, got {v_decimal}")
        return v_decimal


class AnnexIVLeverageInput(BaseModel):
    """Input to Annex IV leverage builder.

    Contains already-computed leverage measures.
    The reporting layer does NOT calculate leverage.

    Fields:
    - gross_leverage_ratio: Gross leverage ratio (Decimal, non-negative, optional).
    - commitment_leverage_ratio: Commitment leverage ratio (Decimal, non-negative, optional).
    - gross_exposure: Gross exposure in base currency (Decimal, non-negative, optional).
    - commitment_exposure: Commitment exposure in base currency (Decimal, non-negative, optional).
    - nav: Net Asset Value (Decimal, non-negative, optional).
    - leverage_methodology: Description of leverage calculation method (str, optional).
    - methodology_version: Version of leverage methodology (str, optional).

    Invariants:
    - All Decimal fields must be non-negative if supplied.
    - leverage_methodology (if supplied) must be non-empty.
    - At least one leverage measure should be supplied (not enforced here, validation at use).
    """

    gross_leverage_ratio: Optional[Decimal] = None
    commitment_leverage_ratio: Optional[Decimal] = None
    gross_exposure: Optional[Decimal] = None
    commitment_exposure: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    leverage_methodology: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("gross_leverage_ratio")
    @classmethod
    def validate_gross_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross leverage ratio must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"gross_leverage_ratio must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("commitment_leverage_ratio")
    @classmethod
    def validate_commitment_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment leverage ratio must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"commitment_leverage_ratio must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"gross_exposure must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"commitment_exposure must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """NAV must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"nav must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("leverage_methodology")
    @classmethod
    def validate_leverage_methodology(cls, v: Optional[str]) -> Optional[str]:
        """Leverage methodology must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("leverage_methodology must be non-empty")
        return v.strip()


class AnnexIVLeverageSection(BaseModel):
    """Result of Annex IV leverage assembly.

    Immutable leverage section for Annex IV reporting.
    Contains already-computed leverage measures.

    Fields:
    - gross_leverage_ratio: Gross leverage ratio (Decimal, optional).
    - commitment_leverage_ratio: Commitment leverage ratio (Decimal, optional).
    - gross_exposure: Gross exposure in base currency (Decimal, optional).
    - commitment_exposure: Commitment exposure in base currency (Decimal, optional).
    - nav: Net Asset Value (Decimal, optional).
    - leverage_methodology: Description of leverage calculation method (str, optional).
    - methodology_version: Version of leverage methodology (str, optional).

    Invariants (defensive checks):
    - All Decimal fields must be non-negative if supplied.
    - leverage_methodology (if supplied) must be non-empty.
    """

    gross_leverage_ratio: Optional[Decimal] = None
    commitment_leverage_ratio: Optional[Decimal] = None
    gross_exposure: Optional[Decimal] = None
    commitment_exposure: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    leverage_methodology: Optional[str] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("gross_leverage_ratio")
    @classmethod
    def validate_gross_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross leverage ratio must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"gross_leverage_ratio must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("commitment_leverage_ratio")
    @classmethod
    def validate_commitment_leverage_ratio(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment leverage ratio must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"commitment_leverage_ratio must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("gross_exposure")
    @classmethod
    def validate_gross_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Gross exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"gross_exposure must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("commitment_exposure")
    @classmethod
    def validate_commitment_exposure(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Commitment exposure must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"commitment_exposure must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """NAV must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"nav must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("leverage_methodology")
    @classmethod
    def validate_leverage_methodology(cls, v: Optional[str]) -> Optional[str]:
        """Leverage methodology must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("leverage_methodology must be non-empty")
        return v


class AnnexIVLiquidityProfileInput(BaseModel):
    """Input to Annex IV liquidity profile builder.

    Contains already-computed liquidity information.
    The reporting layer does NOT calculate liquidity metrics.

    Fields:
    - redemption_frequency: Redemption frequency description (str, non-empty).
    - notice_period_days: Notice period in days (int, non-negative).
    - settlement_period_days: Settlement period in days (int, non-negative).
    - liquidity_profile_description: Overall liquidity profile description (str, optional).
    - liquidity_bucket_summary: Summary of liquidity buckets (str, optional).
    - average_time_to_liquidate_days: Average time-to-liquidate in days (Decimal, optional).
    - methodology_version: Version of liquidity methodology (str, optional).

    Invariants:
    - redemption_frequency must be non-empty.
    - notice_period_days must be non-negative.
    - settlement_period_days must be non-negative.
    - average_time_to_liquidate_days (if supplied) must be non-negative.
    - Optional strings (if supplied) must be non-empty.
    """

    redemption_frequency: str
    notice_period_days: int
    settlement_period_days: int
    liquidity_profile_description: Optional[str] = None
    liquidity_bucket_summary: Optional[str] = None
    average_time_to_liquidate_days: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("redemption_frequency")
    @classmethod
    def validate_redemption_frequency(cls, v: str) -> str:
        """Redemption frequency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("redemption_frequency must be non-empty")
        return v.strip()

    @field_validator("notice_period_days")
    @classmethod
    def validate_notice_period_days(cls, v: int) -> int:
        """Notice period must be non-negative."""
        if v < 0:
            raise ValueError(f"notice_period_days must be non-negative, got {v}")
        return v

    @field_validator("settlement_period_days")
    @classmethod
    def validate_settlement_period_days(cls, v: int) -> int:
        """Settlement period must be non-negative."""
        if v < 0:
            raise ValueError(f"settlement_period_days must be non-negative, got {v}")
        return v

    @field_validator("liquidity_profile_description")
    @classmethod
    def validate_liquidity_profile_description(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity profile description must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("liquidity_profile_description must be non-empty")
        return v.strip()

    @field_validator("liquidity_bucket_summary")
    @classmethod
    def validate_liquidity_bucket_summary(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity bucket summary must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("liquidity_bucket_summary must be non-empty")
        return v.strip()

    @field_validator("average_time_to_liquidate_days")
    @classmethod
    def validate_average_time_to_liquidate_days(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Average time-to-liquidate must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(
                f"average_time_to_liquidate_days must be non-negative, got {v_decimal}"
            )
        return v_decimal


class AnnexIVLiquidityProfileSection(BaseModel):
    """Result of Annex IV liquidity profile assembly.

    Immutable liquidity profile section for Annex IV reporting.
    Contains already-computed liquidity information.

    Fields:
    - redemption_frequency: Redemption frequency description (str).
    - notice_period_days: Notice period in days (int).
    - settlement_period_days: Settlement period in days (int).
    - liquidity_profile_description: Overall liquidity profile description (str, optional).
    - liquidity_bucket_summary: Summary of liquidity buckets (str, optional).
    - average_time_to_liquidate_days: Average time-to-liquidate in days (Decimal, optional).
    - methodology_version: Version of liquidity methodology (str, optional).

    Invariants (defensive checks):
    - redemption_frequency must be non-empty.
    - notice_period_days must be non-negative.
    - settlement_period_days must be non-negative.
    - average_time_to_liquidate_days (if supplied) must be non-negative.
    - Optional strings (if supplied) must be non-empty.
    """

    redemption_frequency: str
    notice_period_days: int
    settlement_period_days: int
    liquidity_profile_description: Optional[str] = None
    liquidity_bucket_summary: Optional[str] = None
    average_time_to_liquidate_days: Optional[Decimal] = None
    methodology_version: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("redemption_frequency")
    @classmethod
    def validate_redemption_frequency(cls, v: str) -> str:
        """Redemption frequency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("redemption_frequency must be non-empty")
        return v

    @field_validator("notice_period_days")
    @classmethod
    def validate_notice_period_days(cls, v: int) -> int:
        """Notice period must be non-negative."""
        if v < 0:
            raise ValueError(f"notice_period_days must be non-negative, got {v}")
        return v

    @field_validator("settlement_period_days")
    @classmethod
    def validate_settlement_period_days(cls, v: int) -> int:
        """Settlement period must be non-negative."""
        if v < 0:
            raise ValueError(f"settlement_period_days must be non-negative, got {v}")
        return v

    @field_validator("liquidity_profile_description")
    @classmethod
    def validate_liquidity_profile_description(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity profile description must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("liquidity_profile_description must be non-empty")
        return v

    @field_validator("liquidity_bucket_summary")
    @classmethod
    def validate_liquidity_bucket_summary(cls, v: Optional[str]) -> Optional[str]:
        """Liquidity bucket summary must be non-empty if supplied."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("liquidity_bucket_summary must be non-empty")
        return v

    @field_validator("average_time_to_liquidate_days")
    @classmethod
    def validate_average_time_to_liquidate_days(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Average time-to-liquidate must be non-negative if supplied."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(
                f"average_time_to_liquidate_days must be non-negative, got {v_decimal}"
            )
        return v_decimal


class AnnexIVReport(BaseModel):
    """Annex IV-style reporting container.

    Immutable report that assembles all Annex IV sections.
    Contains fund identification, optionally asset breakdown, risk measures, leverage,
    and liquidity profile.

    This is the complete Annex IV reporting implementation for Issue #12.

    Fields:
    - fund_identification: Fund identification section.
    - asset_breakdown: Optional asset breakdown section.
    - risk_measures: Optional risk measures section.
    - leverage: Optional leverage section.
    - liquidity_profile: Optional liquidity profile section.
    - included_sections: List of included report sections (informational).

    Invariants (defensive checks):
    - fund_identification must be present.
    - included_sections must list "Fund Identification".
    - If asset_breakdown is supplied, included_sections must include "Asset Breakdown".
    - If risk_measures is supplied, included_sections must include "Risk Measures".
    - If leverage is supplied, included_sections must include "Leverage".
    - If liquidity_profile is supplied, included_sections must include "Liquidity Profile".
    """

    fund_identification: AnnexIVFundIdentificationSection
    asset_breakdown: Optional[AnnexIVAssetBreakdownSection] = None
    risk_measures: Optional[AnnexIVRiskMeasuresSection] = None
    leverage: Optional[AnnexIVLeverageSection] = None
    liquidity_profile: Optional[AnnexIVLiquidityProfileSection] = None
    included_sections: list[str]

    model_config = ConfigDict(frozen=True)

    @field_validator("included_sections")
    @classmethod
    def validate_included_sections(cls, v: list[str]) -> list[str]:
        """included_sections must contain Fund Identification."""
        if "Fund Identification" not in v:
            raise ValueError("Fund Identification must be in included_sections")
        return v
