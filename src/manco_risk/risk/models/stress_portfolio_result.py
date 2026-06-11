"""Result model for a portfolio under a stress scenario.

Represents the stressed NAV, P&L, and individual position results.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.models.stress_position_result import StressPositionResult


class StressPortfolioResult(BaseModel):
    """Stressed outcome for a portfolio under one scenario.

    Represents:
    - scenario identification and metadata
    - current and stressed NAV
    - portfolio-level P&L and loss percentage
    - individual position results
    - position counts for auditing

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date of the portfolio snapshot.
    - scenario_id: Stress scenario identifier (e.g., "EQ_PARALLEL_20").
    - scenario_name: Human-readable scenario name.
    - scenario_type: Scenario type (e.g., "HYPOTHETICAL").
    - scenario_source: Scenario source (e.g., "MANAGER_DEFINED").
    - shock_type: Shock type (e.g., "PARALLEL_EQUITY").
    - shock_rate: Shock rate applied (decimal, e.g., -0.20).
    - current_nav: Current NAV before stress.
    - stressed_nav: NAV after stress.
    - total_pnl: Portfolio-level P&L (signed).
    - loss_pct_nav: Loss as percentage of current NAV (non-negative).
    - stressed_positions: List of individual stressed position results.
    - num_positions_stressed: Count of positions stressed (supported asset classes).
    - num_cash_positions: Count of cash positions (unchanged).

    Sign convention:
    - total_pnl is signed: negative = loss, positive = gain.
    - loss_pct_nav is always non-negative: max(0, -total_pnl / current_nav).

    Formulas:
    - stressed_nav = current_nav + total_pnl
    - loss_pct_nav = max(0, -total_pnl / current_nav)

    Special cases:
    - All-cash portfolio is valid: total_pnl = 0, loss_pct_nav = 0.
    - Positive shock produces gain: total_pnl > 0, loss_pct_nav = 0.

    Immutability:
    - Frozen; result is immutable after construction.
    """

    fund_id: int
    valuation_date: date
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    shock_type: str
    shock_rate: Decimal
    current_nav: Decimal
    stressed_nav: Decimal
    total_pnl: Decimal
    loss_pct_nav: Decimal
    stressed_positions: list[StressPositionResult]
    num_positions_stressed: int
    num_cash_positions: int

    model_config = ConfigDict(frozen=True)

    @field_validator("current_nav", "stressed_nav")
    @classmethod
    def validate_non_negative_nav(cls, v: Decimal) -> Decimal:
        """NAV values must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"NAV must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("loss_pct_nav")
    @classmethod
    def validate_loss_pct_nav(cls, v: Decimal) -> Decimal:
        """Loss percentage must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Loss percentage must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("shock_rate", "total_pnl", mode="before")
    @classmethod
    def validate_decimal_conversion(cls, v) -> Decimal:
        """Ensure decimal fields are valid Decimals."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Value must be convertible to Decimal, got {v}: {e}")

    @field_validator("num_positions_stressed", "num_cash_positions")
    @classmethod
    def validate_non_negative_counts(cls, v: int) -> int:
        """Position counts must be non-negative."""
        if v < 0:
            raise ValueError(f"Position count must be non-negative, got {v}")
        return v
