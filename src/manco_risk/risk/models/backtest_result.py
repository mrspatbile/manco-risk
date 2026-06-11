"""Output model for VaR backtesting.

Regulatory counts and diagnostic information from VaR backtesting alignment and counting.
Phase 1 focuses on observation alignment and explicit counting.
Statistical tests (Kupiec, Christoffersen) are deferred to later phases.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class BacktestObservation(BaseModel):
    """Single aligned VaR forecast and realised P&L pair.

    Represents one day in the backtest where both a VaR forecast and
    realised P&L are available for comparison.

    Fields:
    - observation_date: The date of the observation (common to forecast and realisation).
    - var_value: VaR forecast (positive loss magnitude).
    - realised_pnl: Realised portfolio P&L (signed).
    - is_breach: True if realised_pnl < -var_value (strict inequality).

    Sign convention:
    - var_value: always non-negative (loss magnitude).
    - realised_pnl: signed (positive = gain, negative = loss).
    - Breach occurs when realised_pnl < -var_value (strictly).
    - Exact threshold hit (realised_pnl == -var_value) is NOT a breach.
    """

    observation_date: date
    var_value: Decimal
    realised_pnl: Decimal
    is_breach: bool

    model_config = ConfigDict(frozen=True)

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"VaR value must be non-negative, got {v_decimal}")
        return v_decimal


class BacktestResult(BaseModel):
    """Result of VaR backtesting: regulatory counts and diagnostics.

    Summarizes the alignment of VaR forecasts with realised P&Ls and computes
    explicit counts for regulatory backtesting requirements.

    Phase 1 focuses on:
    - Observation alignment by date
    - Breach detection
    - Regulatory counting
    - Missing data identification

    Statistical tests (Kupiec, Christoffersen) are deferred to later phases.

    Core regulatory counts:
    - num_var_forecasts: Total VaR forecasts available.
    - num_pnl_observations: Total realised P&L observations available.
    - num_valid_aligned: Number of dates where both VaR and P&L are present.
    - num_breaches: Count of dates where realised_pnl < -var_value (strict).
    - num_non_breaches: num_valid_aligned - num_breaches.

    Ratios and expectations:
    - breach_ratio: num_breaches / num_valid_aligned (if num_valid_aligned > 0).
    - expected_breach_probability: 1 - confidence_level.
    - expected_breach_count: num_valid_aligned * (1 - confidence_level).

    Diagnostics:
    - backtest_start_date: Earliest date in valid aligned observations.
    - backtest_end_date: Latest date in valid aligned observations.
    - breach_dates: List of dates where breaches occurred.
    - missing_var_dates: Dates where P&L exists but VaR is missing.
    - missing_pnl_dates: Dates where VaR exists but P&L is missing.
    - aligned_observations: List of BacktestObservation objects (for detailed analysis).

    Invariants:
    - num_breaches + num_non_breaches == num_valid_aligned
    - breach_ratio = num_breaches / num_valid_aligned (if num_valid_aligned > 0)
    - len(breach_dates) == num_breaches
    - if num_valid_aligned == 0, breach_ratio = None (undefined) and backtest dates span full range
    """

    num_var_forecasts: int
    num_pnl_observations: int
    num_valid_aligned: int
    num_breaches: int
    num_non_breaches: int
    expected_breach_probability: Decimal
    expected_breach_count: Decimal
    breach_ratio: Decimal | None
    backtest_start_date: date | None
    backtest_end_date: date | None
    breach_dates: list[date]
    missing_var_dates: list[date]
    missing_pnl_dates: list[date]
    aligned_observations: list[BacktestObservation]

    model_config = ConfigDict(frozen=True)

    @field_validator("num_var_forecasts")
    @classmethod
    def validate_num_var_forecasts(cls, v: int) -> int:
        """Number of VaR forecasts must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of VaR forecasts must be non-negative, got {v}")
        return v

    @field_validator("num_pnl_observations")
    @classmethod
    def validate_num_pnl_observations(cls, v: int) -> int:
        """Number of realised P&L observations must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of realised P&L observations must be non-negative, got {v}")
        return v

    @field_validator("num_valid_aligned")
    @classmethod
    def validate_num_valid_aligned(cls, v: int) -> int:
        """Number of valid aligned observations must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of valid aligned observations must be non-negative, got {v}")
        return v

    @field_validator("num_breaches")
    @classmethod
    def validate_num_breaches(cls, v: int) -> int:
        """Number of breaches must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of breaches must be non-negative, got {v}")
        return v

    @field_validator("num_non_breaches")
    @classmethod
    def validate_num_non_breaches(cls, v: int) -> int:
        """Number of non-breaches must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of non-breaches must be non-negative, got {v}")
        return v

    @field_validator("expected_breach_probability")
    @classmethod
    def validate_expected_breach_probability(cls, v: Decimal) -> Decimal:
        """Expected breach probability must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"Expected breach probability must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("expected_breach_count")
    @classmethod
    def validate_expected_breach_count(cls, v: Decimal) -> Decimal:
        """Expected breach count must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Expected breach count must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("breach_ratio")
    @classmethod
    def validate_breach_ratio(cls, v: Decimal | None) -> Decimal | None:
        """Breach ratio must be in [0, 1] or None."""
        if v is None:
            return v
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"Breach ratio must be in [0, 1] or None, got {v_decimal}")
        return v_decimal

    @field_validator("aligned_observations", mode="after")
    @classmethod
    def validate_aligned_observations_count(
        cls, v: list[BacktestObservation], info
    ) -> list[BacktestObservation]:
        """Number of aligned observations must match num_valid_aligned."""
        if "num_valid_aligned" in info.data and len(v) != info.data["num_valid_aligned"]:
            raise ValueError(
                f"aligned_observations count {len(v)} does not match "
                f"num_valid_aligned {info.data['num_valid_aligned']}"
            )
        return v

    @field_validator("breach_dates", mode="after")
    @classmethod
    def validate_breach_dates_count(cls, v: list[date], info) -> list[date]:
        """Number of breach dates must match num_breaches."""
        if "num_breaches" in info.data and len(v) != info.data["num_breaches"]:
            raise ValueError(
                f"breach_dates count {len(v)} does not match num_breaches {info.data['num_breaches']}"
            )
        return v

    @field_validator("num_breaches", mode="after")
    @classmethod
    def validate_breach_count_consistency(cls, v: int, info) -> int:
        """num_breaches + num_non_breaches must equal num_valid_aligned."""
        if "num_non_breaches" in info.data and "num_valid_aligned" in info.data:
            total = v + info.data["num_non_breaches"]
            if total != info.data["num_valid_aligned"]:
                raise ValueError(
                    f"num_breaches ({v}) + num_non_breaches ({info.data['num_non_breaches']}) "
                    f"must equal num_valid_aligned ({info.data['num_valid_aligned']})"
                )
        return v
