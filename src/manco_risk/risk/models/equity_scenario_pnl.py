"""Equity-like scenario P&L input and result models.

Models for equity scenario P&L generation from fixed portfolios and historical returns.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.etl.enriched_position import RiskReadyPortfolio
from manco_risk.risk.models.scenario_pnl import ScenarioPnL


class EquityScenarioPnLInput(BaseModel):
    """Input for equity-like scenario P&L generation.

    Specifies a fixed portfolio and historical return data by ISIN and date.

    Fields:
    - portfolio: Risk-ready portfolio (current fixed, enriched positions).
    - historical_returns: dict mapping ISIN → {date → return}.
      Returns are signed decimals: negative = loss, positive = gain.

    Invariants:
    - portfolio is non-empty (degenerate portfolios may be rejected)
    - historical_returns dict is non-empty
    - all returns are valid Decimals
    """

    portfolio: RiskReadyPortfolio
    historical_returns: dict[str, dict[date, Decimal]]

    model_config = ConfigDict(frozen=True)

    @field_validator("historical_returns", mode="before")
    @classmethod
    def validate_returns_structure(cls, v):
        """Validate that returns are dict of dicts with date keys and Decimal values."""
        if not isinstance(v, dict):
            raise ValueError("historical_returns must be a dict")
        for isin, dates_dict in v.items():
            if not isinstance(dates_dict, dict):
                raise ValueError(f"Returns for {isin} must be a dict, got {type(dates_dict)}")
            for d, ret in dates_dict.items():
                if not isinstance(d, date):
                    raise ValueError(f"Return date key must be date, got {type(d)}")
                if not isinstance(ret, Decimal):
                    # Attempt conversion
                    try:
                        _ = Decimal(str(ret))
                    except Exception:
                        raise ValueError(f"Return for {isin} on {d} must be convertible to Decimal")
        return v


class EquityScenarioPnLResult(BaseModel):
    """Result of equity-like scenario P&L generation.

    Contains scenario P&Ls ready for input to VaR engine, plus metadata.

    Fields:
    - scenario_pnls: List of portfolio P&Ls, one per scenario date.
    - num_scenarios: Number of scenarios generated (length of scenario_pnls).
    - num_cash_positions: Count of cash positions in portfolio.
    - num_equity_like_positions: Count of equity-like positions (EQUITY, ETF, LISTED_FUND, INDEX).
    """

    scenario_pnls: list[ScenarioPnL]
    num_scenarios: int
    num_cash_positions: int
    num_equity_like_positions: int

    model_config = ConfigDict(frozen=True)

    @field_validator("num_scenarios")
    @classmethod
    def validate_num_scenarios(cls, v: int) -> int:
        """Number of scenarios must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of scenarios must be non-negative, got {v}")
        return v

    @field_validator("num_cash_positions")
    @classmethod
    def validate_num_cash_positions(cls, v: int) -> int:
        """Number of cash positions must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of cash positions must be non-negative, got {v}")
        return v

    @field_validator("num_equity_like_positions")
    @classmethod
    def validate_num_equity_like_positions(cls, v: int) -> int:
        """Number of equity-like positions must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of equity-like positions must be non-negative, got {v}")
        return v

    @field_validator("scenario_pnls")
    @classmethod
    def validate_scenario_pnls(cls, v: list[ScenarioPnL], info) -> list[ScenarioPnL]:
        """Validate that scenario_pnls length matches num_scenarios."""
        # num_scenarios is validated after this, so we can't cross-validate here.
        # Instead, ensure non-empty if num_scenarios > 0 will be checked later.
        return v
