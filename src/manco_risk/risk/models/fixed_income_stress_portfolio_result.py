"""Result model for a portfolio under a fixed-income stress scenario.

Aggregates position-level results and provides portfolio-level P&L decomposition.

Dirty value convention (Phase 1):
    current_nav and stressed_nav are computed using market_value_base_ccy
    as the dirty market value proxy. See fixed_income_stress_position_result.py.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)


class FixedIncomeStressPortfolioResult(BaseModel):
    """Stressed outcome for a portfolio under one fixed-income scenario.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date of the portfolio snapshot.
    - scenario_id: Scenario identifier (e.g., "FI_RATE_UP_100").
    - scenario_name: Human-readable scenario name.
    - scenario_type: Scenario type (e.g., "HYPOTHETICAL").
    - scenario_source: Scenario source (e.g., "MANAGER_DEFINED").
    - shock_type: Audit label (e.g., "RATE_SHOCK", "SPREAD_SHOCK", "COMBINED").
    - rate_shock_bps: Yield shock applied in integer basis points.
    - spread_shock_bps: Spread shock applied in integer basis points.
    - current_nav: Current NAV before stress (non-negative).
    - stressed_nav: NAV after stress (non-negative).
    - total_rate_pnl: Aggregate rate P&L across all positions (signed).
    - total_credit_pnl: Aggregate credit P&L across all positions (signed).
    - total_pnl: total_rate_pnl + total_credit_pnl (signed).
    - loss_pct_nav: Loss as fraction of current_nav (non-negative; 0 for gain).
    - stressed_positions: Individual position results.
    - num_bond_positions: Count of bond positions stressed.
    - num_cash_positions: Count of cash positions (unchanged).

    Sign conventions:
    - total_pnl is signed: negative = loss, positive = gain.
    - loss_pct_nav = max(0, -total_pnl / current_nav).

    Formulas:
    - stressed_nav = current_nav + total_pnl
    - loss_pct_nav = max(0, -total_pnl / current_nav)

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
    rate_shock_bps: int
    spread_shock_bps: int
    current_nav: Decimal
    stressed_nav: Decimal
    total_rate_pnl: Decimal
    total_credit_pnl: Decimal
    total_pnl: Decimal
    loss_pct_nav: Decimal
    stressed_positions: list[FixedIncomeStressPositionResult]
    num_bond_positions: int
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

    @field_validator("total_rate_pnl", "total_credit_pnl", "total_pnl", mode="before")
    @classmethod
    def validate_decimal_conversion(cls, v) -> Decimal:
        """Ensure P&L fields are valid Decimals."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Value must be convertible to Decimal, got {v}: {e}")

    @field_validator("num_bond_positions", "num_cash_positions")
    @classmethod
    def validate_non_negative_counts(cls, v: int) -> int:
        """Position counts must be non-negative."""
        if v < 0:
            raise ValueError(f"Position count must be non-negative, got {v}")
        return v
