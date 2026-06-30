"""PRIIPs Cost Table models.

Pure data models. No calculation or persistence logic.

Commission Delegated Regulation (EU) 2017/653 Annex VI/VII defines cost
tables as pre-computed cost breakdowns across entry, exit, ongoing,
transaction, and incidental components.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class PRIIPSCostsInput(BaseModel):
    """Input to PRIIPs Costs engine.

    Minimal input containing pre-computed cost values for a product
    at a point in time.

    This model expects cost values to be calculated externally.
    The engine validates inputs and returns export-ready results.

    Fields:
    - product_id: Product identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - methodology_version: PRIIPs RTS version (e.g., "2017/653", "2021/2268").
    - recommended_holding_period_years: RHP in years (positive integer).
    - entry_cost: Entry cost as decimal (e.g., 0.01 = 1%).
    - exit_cost: Exit cost as decimal (e.g., 0.005 = 0.5%).
    - ongoing_cost: Ongoing charge as decimal (e.g., 0.005 = 0.5% per year).
    - transaction_cost: Transaction cost as decimal (e.g., 0.001 = 0.1%).
    - incidental_cost: Incidental cost as decimal (e.g., 0.0 = 0%).

    Invariants:
    - product_id must be non-empty.
    - methodology_version must be non-empty.
    - recommended_holding_period_years must be positive.
    - All costs must be Decimal (no None values).
    - Costs may be zero or positive; negative values are accepted as pre-computed inputs.
    """

    product_id: str
    valuation_date: date
    methodology_version: str
    recommended_holding_period_years: int
    entry_cost: Decimal | float | int | str
    exit_cost: Decimal | float | int | str
    ongoing_cost: Decimal | float | int | str
    transaction_cost: Decimal | float | int | str
    incidental_cost: Decimal | float | int | str

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
        "entry_cost",
        "exit_cost",
        "ongoing_cost",
        "transaction_cost",
        "incidental_cost",
        mode="before",
    )
    @classmethod
    def coerce_decimal(cls, v: Decimal | float | int | str) -> Decimal:
        """Coerce numeric types to Decimal for precision."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class PRIIPSCostsResult(BaseModel):
    """Result of PRIIPs Costs packaging.

    Contains pre-computed cost values organised for PRIIPs KID output.

    This model is a simple immutable DTO with minimal defensive validation.

    Fields:
    - product_id: Product identifier.
    - valuation_date: Snapshot date.
    - methodology_version: PRIIPs RTS version (preserved from input).
    - recommended_holding_period_years: RHP in years.
    - entry_cost: Entry cost (Decimal).
    - exit_cost: Exit cost (Decimal).
    - ongoing_cost: Ongoing charge (Decimal).
    - transaction_cost: Transaction cost (Decimal).
    - incidental_cost: Incidental cost (Decimal).

    Invariants (defensive checks):
    - product_id must be non-empty.
    - methodology_version must be non-empty.
    - recommended_holding_period_years must be positive.
    - All costs must be Decimal.
    """

    product_id: str
    valuation_date: date
    methodology_version: str
    recommended_holding_period_years: int
    entry_cost: Decimal
    exit_cost: Decimal
    ongoing_cost: Decimal
    transaction_cost: Decimal
    incidental_cost: Decimal

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

    @field_validator(
        "entry_cost", "exit_cost", "ongoing_cost", "transaction_cost", "incidental_cost"
    )
    @classmethod
    def validate_cost_is_decimal(cls, v: Decimal) -> Decimal:
        """Cost must be Decimal (defensive check)."""
        if not isinstance(v, Decimal):
            raise ValueError(f"cost must be Decimal, got {type(v).__name__}")
        return v
