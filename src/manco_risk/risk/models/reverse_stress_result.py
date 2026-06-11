"""Result model for reverse equity stress calculation.

Represents the calculated shock required to reach a target NAV loss,
or infeasibility reason if the target cannot be reached.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from manco_risk.risk.models.stress_portfolio_result import StressPortfolioResult


class ReverseStressResult(BaseModel):
    """Result of reverse equity stress calculation.

    Represents the calculated parallel equity shock needed to reach a target NAV loss,
    plus diagnostics and the underlying stress result if feasible.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date of the portfolio snapshot.
    - scenario_id: Scenario identifier.
    - scenario_name: Human-readable scenario name.
    - scenario_type: Always "REVERSE" for reverse stress results.
    - scenario_source: Scenario source (from input or calculated).
    - target_loss_pct: Target NAV loss (from input).
    - target_loss_amount: Calculated loss amount in base currency (nav * target_loss_pct).
    - equity_like_market_value: Sum of current equity-like position values.
    - required_shock: Calculated shock rate (decimal) needed to reach target.
                      None if zero equity-like exposure (cannot calculate).
                      Populated even if infeasible (e.g., shock < -1.0) for diagnostics.
    - is_feasible: True if target can be reached; False if infeasible or zero equity exposure.
    - infeasibility_reason: Human-readable explanation if is_feasible=False; else None.
    - stress_result: StressPortfolioResult if feasible, else None.

    Feasibility rules:
    - Feasible if required_shock is in range [-1.0, +inf) (shock can be applied).
    - Infeasible if:
      * zero equity-like exposure (required_shock=None, cannot calculate)
      * required_shock < -1.0 (exceeds -100%, not applicable; required_shock kept for diagnostics)
      * target_loss_amount >= current_nav (wipes out entire fund)

    Sign convention:
    - target_loss_pct is non-negative (e.g., 0.20 = 20% loss).
    - required_shock is typically negative for loss scenarios (e.g., -0.25 = 25% down).
    - required_shock = 0 is feasible (no shock needed to reach 0% loss).

    Immutability:
    - Frozen; result is immutable after construction.
    """

    fund_id: int
    valuation_date: date
    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    target_loss_pct: Decimal
    target_loss_amount: Decimal
    equity_like_market_value: Decimal
    required_shock: Optional[Decimal] = None
    is_feasible: bool
    infeasibility_reason: Optional[str] = None
    stress_result: Optional[StressPortfolioResult] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("target_loss_pct")
    @classmethod
    def validate_target_loss_pct(cls, v: Decimal) -> Decimal:
        """Target loss percentage must be >= 0 and < 1."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"target_loss_pct must be >= 0, got {v_decimal}")
        if v_decimal >= Decimal("1"):
            raise ValueError(f"target_loss_pct must be < 1, got {v_decimal}")
        return v_decimal

    @field_validator("target_loss_amount", "equity_like_market_value")
    @classmethod
    def validate_non_negative_amounts(cls, v: Decimal) -> Decimal:
        """Monetary amounts must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Amount must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("required_shock", mode="before")
    @classmethod
    def validate_required_shock(cls, v) -> Optional[Decimal]:
        """Required shock must be a valid Decimal or None."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"required_shock must be convertible to Decimal or None, got {v}: {e}")

    @model_validator(mode="after")
    def validate_feasibility_consistency(self) -> "ReverseStressResult":
        """Validate consistency between is_feasible, stress_result, and required_shock."""
        if self.is_feasible:
            # If feasible, stress_result must be populated
            if self.stress_result is None:
                raise ValueError("If is_feasible=True, stress_result must be populated")
        else:
            # If infeasible, stress_result must be None
            if self.stress_result is not None:
                raise ValueError("If is_feasible=False, stress_result must be None")

        return self
