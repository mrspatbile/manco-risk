"""Result model for a portfolio under a combined multi-asset stress scenario.

Aggregates equity-like and fixed-income sub-results into a single portfolio view.
Cash is handled at combined level with zero P&L; cash positions are reflected
in num_cash_positions and cash_value_base_ccy but do not appear in either sub-result.

Aggregation formulas:
    equity_pnl   = equity_result.total_pnl if equity_result else Decimal("0")
    fi_pnl       = fi_result.total_pnl     if fi_result     else Decimal("0")
    total_pnl    = equity_pnl + fi_pnl
    stressed_nav = current_nav + total_pnl
    loss_pct_nav = max(0, -total_pnl / current_nav)
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult


class CombinedStressPortfolioResult(BaseModel):
    """Stressed outcome for a portfolio under one combined stress scenario.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date of the portfolio snapshot.
    - scenario_id: Combined scenario identifier.
    - scenario_name: Human-readable combined scenario name.
    - scenario_type: Scenario type (e.g. "HYPOTHETICAL").
    - scenario_source: Scenario source (e.g. "MANAGER_DEFINED").
    - current_nav: Fund NAV before stress (non-negative).
    - stressed_nav: Fund NAV after combined stress (non-negative).
    - total_pnl: Combined P&L: equity_pnl + fi_pnl (signed).
    - loss_pct_nav: Loss as fraction of current_nav (non-negative; 0 for gain).
    - num_cash_positions: Count of base-currency cash positions (unchanged, zero P&L).
    - cash_value_base_ccy: Total base-currency value of cash positions.
    - equity_result: Equity-like sub-result; None if no equity scenario or no equity positions.
    - fi_result: Fixed-income sub-result; None if no FI scenario or no bond positions.

    Sign conventions:
    - total_pnl: negative = loss, positive = gain.
    - loss_pct_nav = max(0, -total_pnl / current_nav).

    Immutability:
    - Frozen; result is immutable after construction.
    """

    fund_id: int
    valuation_date: date
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    current_nav: Decimal
    stressed_nav: Decimal
    total_pnl: Decimal
    loss_pct_nav: Decimal
    num_cash_positions: int
    cash_value_base_ccy: Decimal
    equity_result: StressPortfolioResult | None
    fi_result: FixedIncomeStressPortfolioResult | None

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

    @field_validator("total_pnl", "cash_value_base_ccy", mode="before")
    @classmethod
    def validate_decimal_conversion(cls, v: object) -> Decimal:
        """Ensure monetary fields are valid Decimals."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"Value must be convertible to Decimal, got {v}: {e}")

    @field_validator("num_cash_positions")
    @classmethod
    def validate_non_negative_count(cls, v: int) -> int:
        """Cash position count must be non-negative."""
        if v < 0:
            raise ValueError(f"num_cash_positions must be non-negative, got {v}")
        return v
