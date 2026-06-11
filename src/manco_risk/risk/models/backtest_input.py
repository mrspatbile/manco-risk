"""Input models for VaR backtesting.

Represents time series of VaR forecasts and realised P&Ls to be aligned and tested.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class VaRForecastObservation(BaseModel):
    """Single VaR forecast at a valuation date.

    Represents a one-step-ahead VaR forecast made on forecast_date
    for the horizon_days holding period.

    Fields:
    - forecast_date: Date the VaR was calculated/forecasted.
    - var_value: VaR loss threshold (positive, decimal ratio or absolute currency).
    - confidence_level: Confidence level, e.g., 0.95.
    - horizon_days: Holding period in days. Must be 1 for Phase 1.

    Sign convention:
    - var_value is always non-negative (loss magnitude).
    - A 2.5% loss forecast is represented as var_value = Decimal("0.025") (if percentage)
      or as an absolute currency amount.
    """

    forecast_date: date
    var_value: Decimal
    confidence_level: Decimal
    horizon_days: int

    model_config = ConfigDict(frozen=True)

    @field_validator("var_value")
    @classmethod
    def validate_var_value(cls, v: Decimal) -> Decimal:
        """VaR value must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"VaR value must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Confidence level must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v


class RealisedPnLObservation(BaseModel):
    """Single realised portfolio P&L observation.

    Represents the actual portfolio P&L outcome on a given date.

    Fields:
    - pnl_date: Date of the realised P&L outcome.
    - realised_pnl: Signed portfolio P&L (positive = gain, negative = loss).

    Sign convention:
    - positive realised_pnl = gain
    - negative realised_pnl = loss
    - A loss of 2.5% is represented as realised_pnl = Decimal("-0.025") (if percentage)
      or as a negative absolute currency amount.
    """

    pnl_date: date
    realised_pnl: Decimal

    model_config = ConfigDict(frozen=True)


class BacktestInput(BaseModel):
    """Input to the VaR backtesting engine.

    Represents a time series of VaR forecasts and realised P&Ls ready for
    alignment and regulatory counting.

    Fields:
    - var_forecasts: List of VaR forecasts (one per forecast date).
    - realised_pnls: List of realised P&L observations (one per P&L date).
    - confidence_level: Target confidence level for backtesting.
    - horizon_days: Target horizon for backtesting. Must be 1 for Phase 1.

    Validation:
    - At least one VaR forecast required.
    - At least one realised P&L required.
    - No duplicate forecast dates.
    - No duplicate realised P&L dates.
    - All VaR forecasts must match the input confidence_level.
    - All VaR forecasts must match the input horizon_days.
    - horizon_days must be 1 (Phase 1).
    - confidence_level must be in (0, 1).

    Usage:
        >>> var_forecasts = [
        ...     VaRForecastObservation(
        ...         forecast_date=date(2024, 1, 1),
        ...         var_value=Decimal("0.025"),
        ...         confidence_level=Decimal("0.95"),
        ...         horizon_days=1,
        ...     ),
        ... ]
        >>> pnls = [
        ...     RealisedPnLObservation(
        ...         pnl_date=date(2024, 1, 1),
        ...         realised_pnl=Decimal("-0.010"),
        ...     ),
        ... ]
        >>> input = BacktestInput(
        ...     var_forecasts=var_forecasts,
        ...     realised_pnls=pnls,
        ...     confidence_level=Decimal("0.95"),
        ...     horizon_days=1,
        ... )
    """

    var_forecasts: list[VaRForecastObservation]
    realised_pnls: list[RealisedPnLObservation]
    confidence_level: Decimal
    horizon_days: int

    model_config = ConfigDict(frozen=True)

    @field_validator("var_forecasts")
    @classmethod
    def validate_var_forecasts(
        cls, v: list[VaRForecastObservation]
    ) -> list[VaRForecastObservation]:
        """At least one VaR forecast required."""
        if not v:
            raise ValueError("At least one VaR forecast required")
        return v

    @field_validator("realised_pnls")
    @classmethod
    def validate_realised_pnls(
        cls, v: list[RealisedPnLObservation]
    ) -> list[RealisedPnLObservation]:
        """At least one realised P&L required."""
        if not v:
            raise ValueError("At least one realised P&L observation required")
        return v

    @field_validator("var_forecasts", mode="after")
    @classmethod
    def validate_no_duplicate_forecast_dates(
        cls, v: list[VaRForecastObservation]
    ) -> list[VaRForecastObservation]:
        """No duplicate forecast dates allowed."""
        dates = [obs.forecast_date for obs in v]
        if len(dates) != len(set(dates)):
            raise ValueError("Duplicate forecast dates detected")
        return v

    @field_validator("realised_pnls", mode="after")
    @classmethod
    def validate_no_duplicate_pnl_dates(
        cls, v: list[RealisedPnLObservation]
    ) -> list[RealisedPnLObservation]:
        """No duplicate realised P&L dates allowed."""
        dates = [obs.pnl_date for obs in v]
        if len(dates) != len(set(dates)):
            raise ValueError("Duplicate realised P&L dates detected")
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: Decimal) -> Decimal:
        """Confidence level must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Confidence level must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon_days(cls, v: int) -> int:
        """Horizon days must be 1 for Phase 1."""
        if v != 1:
            raise ValueError(f"Phase 1 supports only horizon_days=1, got {v}")
        return v

    @model_validator(mode="after")
    def validate_var_forecasts_match_input_params(self) -> "BacktestInput":
        """All VaR forecasts must match input confidence_level and horizon_days."""
        for obs in self.var_forecasts:
            if obs.confidence_level != self.confidence_level:
                raise ValueError(
                    f"VaR forecast confidence level {obs.confidence_level} "
                    f"does not match input confidence level {self.confidence_level}"
                )
            if obs.horizon_days != self.horizon_days:
                raise ValueError(
                    f"VaR forecast horizon_days {obs.horizon_days} "
                    f"does not match input horizon_days {self.horizon_days}"
                )
        return self
