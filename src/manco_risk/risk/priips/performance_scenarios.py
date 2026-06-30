"""PRIIPs Performance Scenario models.

Pure data models. No calculation or persistence logic.

Commission Delegated Regulation (EU) 2017/653 Annex IV/V defines performance
scenarios as pre-computed projections under stress, unfavourable, moderate,
and favourable market conditions.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class PerformanceScenariosInput(BaseModel):
    """Input to Performance Scenarios engine.

    Minimal input containing pre-computed scenario returns for a product
    at a point in time.

    This model expects scenario values to be calculated externally.
    The engine validates inputs and returns export-ready results.

    Fields:
    - product_id: Product identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - methodology_version: PRIIPs RTS version (e.g., "2017/653", "2021/2268").
    - recommended_holding_period_years: RHP in years (positive integer).
    - stress_return: Stress scenario return (decimal, e.g., -0.25 = -25%).
    - unfavourable_return: Unfavourable scenario return (decimal).
    - moderate_return: Moderate scenario return (decimal).
    - favourable_return: Favourable scenario return (decimal).

    Invariants:
    - product_id must be non-empty.
    - methodology_version must be non-empty.
    - recommended_holding_period_years must be positive.
    - All returns must be Decimal (no None values).
    """

    product_id: str
    valuation_date: date
    methodology_version: str
    recommended_holding_period_years: int
    stress_return: Decimal | float | int | str
    unfavourable_return: Decimal | float | int | str
    moderate_return: Decimal | float | int | str
    favourable_return: Decimal | float | int | str

    model_config = ConfigDict(frozen=True)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Product ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("product_id must be non-empty")
        return v.strip()

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: str) -> str:
        """Methodology version must be non-empty."""
        if not v or not v.strip():
            raise ValueError("methodology_version must be non-empty")
        return v.strip()

    @field_validator("recommended_holding_period_years")
    @classmethod
    def validate_recommended_holding_period_years(cls, v: int) -> int:
        """Recommended holding period must be positive."""
        if v <= 0:
            raise ValueError(f"recommended_holding_period_years must be positive, got {v}")
        return v

    @field_validator(
        "stress_return",
        "unfavourable_return",
        "moderate_return",
        "favourable_return",
        mode="before",
    )
    @classmethod
    def coerce_decimal(cls, v: Decimal | float | int | str) -> Decimal:
        """Coerce numeric types to Decimal for precision."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class PerformanceScenariosResult(BaseModel):
    """Result of Performance Scenarios packaging.

    Contains pre-computed scenario returns organised for PRIIPs KID output.

    This model is a simple immutable DTO with minimal defensive validation.

    Fields:
    - product_id: Product identifier.
    - valuation_date: Snapshot date.
    - methodology_version: PRIIPs RTS version (preserved from input).
    - recommended_holding_period_years: RHP in years.
    - stress_return: Stress scenario return (Decimal).
    - unfavourable_return: Unfavourable scenario return (Decimal).
    - moderate_return: Moderate scenario return (Decimal).
    - favourable_return: Favourable scenario return (Decimal).

    Invariants (defensive checks):
    - product_id must be non-empty.
    - methodology_version must be non-empty.
    - recommended_holding_period_years must be positive.
    - All returns must be Decimal.
    """

    product_id: str
    valuation_date: date
    methodology_version: str
    recommended_holding_period_years: int
    stress_return: Decimal
    unfavourable_return: Decimal
    moderate_return: Decimal
    favourable_return: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Product ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("product_id must be non-empty")
        return v.strip()

    @field_validator("methodology_version")
    @classmethod
    def validate_methodology_version(cls, v: str) -> str:
        """Methodology version must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("methodology_version must be non-empty")
        return v.strip()

    @field_validator("recommended_holding_period_years")
    @classmethod
    def validate_recommended_holding_period_years(cls, v: int) -> int:
        """Recommended holding period must be positive (defensive check)."""
        if v <= 0:
            raise ValueError(f"recommended_holding_period_years must be positive, got {v}")
        return v

    @field_validator("stress_return", "unfavourable_return", "moderate_return", "favourable_return")
    @classmethod
    def validate_return_is_decimal(cls, v: Decimal) -> Decimal:
        """Return must be Decimal (defensive check)."""
        if not isinstance(v, Decimal):
            raise ValueError(f"return must be Decimal, got {type(v).__name__}")
        return v
