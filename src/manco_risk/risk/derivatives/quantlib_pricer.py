"""QuantLib-backed derivative pricer for European equity options.

Implements Black-Scholes-Merton pricing for European calls and puts.
QuantLib is an optional dependency; raises ImportError if not installed.

Uses:
- Flat risk-free curve
- Flat dividend yield curve
- Flat volatility surface
- Actual365Fixed day-count convention
- European exercise

Does NOT include:
- Swap pricing
- Curve bootstrapping
- Vol surfaces
- Exotic options
- Greeks approximations (uses QuantLib analytic Greeks)
"""

from decimal import Decimal
from typing import Any

from manco_risk.risk.derivatives.pricing_models import (
    DerivativePricingResult,
    EuropeanEquityOptionPricingInput,
    OptionType,
)


def _import_quantlib() -> Any:
    """Import QuantLib at runtime with clear error if not installed.

    Returns
    -------
    Any
        The QuantLib module.

    Raises
    ------
    ImportError
        If QuantLib is not installed.
    """
    try:
        import QuantLib as ql  # type: ignore[import-untyped]

        return ql
    except ImportError as exc:
        raise ImportError(
            "QuantLib is required to use QuantLibEuropeanOptionPricer. "
            "Install the optional dependency with: uv sync --extra quantlib"
        ) from exc


class QuantLibEuropeanOptionPricer:
    """European equity option pricer using QuantLib Black-Scholes-Merton.

    Pricing assumptions:
    - Flat risk-free curve at provided rate
    - Flat dividend yield curve at provided rate
    - Flat volatility surface at provided vol
    - Actual365Fixed day-count
    - European exercise (exercise at maturity only)

    Greeks are computed analytically by QuantLib.
    Fair value and Greeks are scaled by quantity.
    """

    def price(self, input: EuropeanEquityOptionPricingInput) -> DerivativePricingResult:
        """Price a European equity option and return Greeks.

        Parameters
        ----------
        input
            European equity option pricing input with spot, strike, rates, vols.

        Returns
        -------
        DerivativePricingResult
            Fair value and Greeks, scaled by quantity.
        """
        ql = _import_quantlib()

        # Convert dates to QuantLib dates
        pricing_date = ql.Date(
            input.pricing_date.day, input.pricing_date.month, input.pricing_date.year
        )
        maturity_date = ql.Date(
            input.maturity_date.day, input.maturity_date.month, input.maturity_date.year
        )
        ql.Settings.instance().evaluationDate = pricing_date

        # Create market data quotes
        spot_quote = ql.SimpleQuote(float(input.spot))
        rf_rate_quote = ql.SimpleQuote(float(input.risk_free_rate))
        div_yield_quote = ql.SimpleQuote(float(input.dividend_yield))
        vol_quote = ql.SimpleQuote(float(input.volatility))

        # Create payoff and option
        option_type_ql = ql.Option.Call if input.option_type == OptionType.CALL else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(option_type_ql, float(input.strike))
        exercise = ql.EuropeanExercise(maturity_date)
        option = ql.VanillaOption(payoff, exercise)

        # Create curves with quotes wrapped in handles
        day_counter = ql.Actual365Fixed()
        rf_handle = ql.QuoteHandle(rf_rate_quote)
        div_handle = ql.QuoteHandle(div_yield_quote)
        vol_handle = ql.QuoteHandle(vol_quote)

        risk_free_curve = ql.YieldTermStructureHandle(
            ql.FlatForward(pricing_date, rf_handle, day_counter)
        )
        dividend_yield_curve = ql.YieldTermStructureHandle(
            ql.FlatForward(pricing_date, div_handle, day_counter)
        )
        volatility_curve = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(pricing_date, ql.TARGET(), vol_handle, day_counter)
        )

        # Create stochastic process (Black-Scholes-Merton includes dividend yield)
        spot_handle = ql.QuoteHandle(spot_quote)
        process = ql.GeneralizedBlackScholesProcess(
            spot_handle, dividend_yield_curve, risk_free_curve, volatility_curve
        )

        # Set pricing engine and compute
        option.setPricingEngine(ql.AnalyticEuropeanEngine(process))

        # Extract outputs
        fair_value = Decimal(str(option.NPV()))
        delta = Decimal(str(option.delta()))
        gamma = Decimal(str(option.gamma()))
        vega = Decimal(str(option.vega()))
        theta = Decimal(str(option.theta()))
        rho = Decimal(str(option.rho()))

        # Scale by quantity
        quantity = input.quantity
        fair_value *= quantity
        delta *= quantity
        gamma *= quantity
        vega *= quantity
        theta *= quantity
        rho *= quantity

        return DerivativePricingResult(
            derivative_id=input.derivative_id,
            pricing_date=input.pricing_date,
            fair_value_base_ccy=fair_value,
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
            rho=rho,
            pricing_model="QuantLib Black-Scholes-Merton",
        )
