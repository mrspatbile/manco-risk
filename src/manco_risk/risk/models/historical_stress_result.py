"""Result model for historical equity stress calculation.

Represents the worst-case scenario from a historical window.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class HistoricalStressResult(BaseModel):
    """Result of historical equity stress calculation.

    Represents the worst-case scenario (maximum loss) from a historical time window.
    Does not apply a shock rate; instead, selects and reports the worst precomputed
    portfolio-level P&L.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Valuation date of the portfolio snapshot.
    - scenario_id: Historical scenario identifier, e.g., "HIST_GFC".
    - scenario_name: Human-readable scenario name.
    - scenario_type: Always "HISTORICAL" for historical stress results.
    - scenario_source: Source of the scenario (from input).
    - shock_type: Type of shock (from input), e.g., "HISTORICAL_EQUITY".
    - window_start_date: Start of historical window (from input).
    - window_end_date: End of historical window (from input).
    - worst_scenario_date: Date of the worst scenario (scenario date of minimum P&L).
    - worst_scenario_pnl: P&L of worst scenario (signed: negative = loss).
    - loss_pct_nav: Loss as percentage of current NAV (non-negative).
    - num_scenarios: Number of scenarios in the window.
    - description: Scenario description (from input).

    Sign convention:
    - worst_scenario_pnl is signed: negative = loss, positive = gain.
    - loss_pct_nav is always non-negative: max(0, -worst_pnl / nav).

    Design:
    - This is a custom result type; does not reuse StressPortfolioResult.
    - Historical stress selects worst scenario; it does not apply a parallel shock.
    - No position-level breakdown (that comes from scenario generation layer).
    - No shock_rate field (historical scenarios are not characterized by a single rate).

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
    window_start_date: date
    window_end_date: date
    worst_scenario_date: date
    worst_scenario_pnl: Decimal
    loss_pct_nav: Decimal
    num_scenarios: int
    description: str
    current_nav: Decimal
    stressed_nav: Decimal

    model_config = ConfigDict(frozen=True)

    @field_validator("loss_pct_nav")
    @classmethod
    def validate_loss_pct_nav(cls, v: Decimal) -> Decimal:
        """Loss percentage must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"loss_pct_nav must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("worst_scenario_pnl", mode="before")
    @classmethod
    def validate_worst_scenario_pnl(cls, v) -> Decimal:
        """Worst scenario P&L must be a valid Decimal."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"worst_scenario_pnl must be convertible to Decimal, got {v}: {e}")

    @field_validator("num_scenarios")
    @classmethod
    def validate_num_scenarios(cls, v: int) -> int:
        """Number of scenarios must be positive."""
        if v <= 0:
            raise ValueError(f"num_scenarios must be positive, got {v}")
        return v

    @field_validator("window_end_date")
    @classmethod
    def validate_window_dates(cls, v: date, info) -> date:
        """Window end date must be >= start date."""
        start_date = info.data.get("window_start_date")
        if start_date and v < start_date:
            raise ValueError(f"window_end_date ({v}) must be >= window_start_date ({start_date})")
        return v

    @model_validator(mode="after")
    def validate_stressed_nav_consistency(self) -> "HistoricalStressResult":
        """Verify stressed_nav = current_nav + worst_scenario_pnl."""
        expected_stressed = self.current_nav + self.worst_scenario_pnl
        if self.stressed_nav != expected_stressed:
            raise ValueError(
                f"stressed_nav ({self.stressed_nav}) must equal "
                f"current_nav ({self.current_nav}) + worst_scenario_pnl ({self.worst_scenario_pnl})"
            )
        return self
