"""Tests for QuantLib-backed European option pricer.

Validates pricing and Greeks calculation for European calls and puts.
Tests use QuantLib's Black-Scholes-Merton model.

Note: These tests are skipped if QuantLib is not installed.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from manco_risk.risk.derivatives import DerivativePricingResult
from manco_risk.risk.derivatives.pricing_models import (
    EuropeanEquityOptionPricingInput,
    OptionType,
)

pytest.importorskip("QuantLib")

from manco_risk.risk.derivatives.quantlib_pricer import QuantLibEuropeanOptionPricer


@pytest.fixture
def valuation_date():
    """Valuation date for pricing."""
    return date(2026, 6, 11)


@pytest.fixture
def standard_call_input(valuation_date):
    """Standard ATM European call option."""
    return EuropeanEquityOptionPricingInput(
        derivative_id="CALL-001",
        pricing_date=valuation_date,
        option_type=OptionType.CALL,
        spot=Decimal("100"),
        strike=Decimal("100"),
        risk_free_rate=Decimal("0.05"),
        dividend_yield=Decimal("0"),
        volatility=Decimal("0.20"),
        maturity_date=valuation_date + timedelta(days=365),
        quantity=Decimal("1"),
    )


@pytest.fixture
def standard_put_input(valuation_date):
    """Standard ATM European put option."""
    return EuropeanEquityOptionPricingInput(
        derivative_id="PUT-001",
        pricing_date=valuation_date,
        option_type=OptionType.PUT,
        spot=Decimal("100"),
        strike=Decimal("100"),
        risk_free_rate=Decimal("0.05"),
        dividend_yield=Decimal("0"),
        volatility=Decimal("0.20"),
        maturity_date=valuation_date + timedelta(days=365),
        quantity=Decimal("1"),
    )


class TestEuropeanEquityOptionInput:
    """Test input model validation."""

    def test_valid_call_input(self, standard_call_input):
        """Valid call input accepted."""
        assert standard_call_input.option_type == OptionType.CALL
        assert standard_call_input.spot == Decimal("100")

    def test_valid_put_input(self, standard_put_input):
        """Valid put input accepted."""
        assert standard_put_input.option_type == OptionType.PUT

    def test_rejects_zero_spot(self, standard_call_input):
        """Zero spot rejected."""
        with pytest.raises(ValueError, match="spot must be positive"):
            EuropeanEquityOptionPricingInput(
                derivative_id="CALL-001",
                pricing_date=standard_call_input.pricing_date,
                option_type=OptionType.CALL,
                spot=Decimal("0"),
                strike=Decimal("100"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0.20"),
                maturity_date=standard_call_input.maturity_date,
            )

    def test_rejects_negative_strike(self, standard_call_input):
        """Negative strike rejected."""
        with pytest.raises(ValueError, match="strike must be positive"):
            EuropeanEquityOptionPricingInput(
                derivative_id="CALL-001",
                pricing_date=standard_call_input.pricing_date,
                option_type=OptionType.CALL,
                spot=Decimal("100"),
                strike=Decimal("-50"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0.20"),
                maturity_date=standard_call_input.maturity_date,
            )

    def test_rejects_zero_volatility(self, standard_call_input):
        """Zero volatility rejected."""
        with pytest.raises(ValueError, match="volatility must be positive"):
            EuropeanEquityOptionPricingInput(
                derivative_id="CALL-001",
                pricing_date=standard_call_input.pricing_date,
                option_type=OptionType.CALL,
                spot=Decimal("100"),
                strike=Decimal("100"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0"),
                maturity_date=standard_call_input.maturity_date,
            )

    def test_rejects_maturity_before_pricing_date(self, valuation_date):
        """Maturity before pricing date rejected."""
        with pytest.raises(ValueError, match="maturity_date.*must be after"):
            EuropeanEquityOptionPricingInput(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                option_type=OptionType.CALL,
                spot=Decimal("100"),
                strike=Decimal("100"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0.20"),
                maturity_date=valuation_date - timedelta(days=1),
            )

    def test_rejects_zero_quantity(self, standard_call_input):
        """Zero quantity rejected."""
        with pytest.raises(ValueError, match="quantity must be non-zero"):
            EuropeanEquityOptionPricingInput(
                derivative_id="CALL-001",
                pricing_date=standard_call_input.pricing_date,
                option_type=OptionType.CALL,
                spot=Decimal("100"),
                strike=Decimal("100"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0.20"),
                maturity_date=standard_call_input.maturity_date,
                quantity=Decimal("0"),
            )

    def test_rejects_empty_derivative_id(self, standard_call_input):
        """Empty derivative_id rejected."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            EuropeanEquityOptionPricingInput(
                derivative_id="",
                pricing_date=standard_call_input.pricing_date,
                option_type=OptionType.CALL,
                spot=Decimal("100"),
                strike=Decimal("100"),
                risk_free_rate=Decimal("0.05"),
                dividend_yield=Decimal("0"),
                volatility=Decimal("0.20"),
                maturity_date=standard_call_input.maturity_date,
            )


class TestQuantLibEuropeanOptionPricer:
    """Test QuantLib pricer."""

    def test_pricer_instantiation(self):
        """Pricer can be instantiated."""
        pricer = QuantLibEuropeanOptionPricer()
        assert pricer is not None

    def test_call_option_prices(self, standard_call_input):
        """European call option prices successfully."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_call_input)

        assert isinstance(result, DerivativePricingResult)
        assert result.derivative_id == "CALL-001"
        assert result.fair_value_base_ccy > Decimal("0")
        assert result.pricing_model == "QuantLib Black-Scholes-Merton"

    def test_put_option_prices(self, standard_put_input):
        """European put option prices successfully."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_put_input)

        assert isinstance(result, DerivativePricingResult)
        assert result.derivative_id == "PUT-001"
        assert result.fair_value_base_ccy > Decimal("0")

    def test_call_delta_positive(self, standard_call_input):
        """Call delta is positive (generally)."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_call_input)

        assert result.delta is not None
        assert result.delta > Decimal("0")

    def test_put_delta_negative(self, standard_put_input):
        """Put delta is negative (generally)."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_put_input)

        assert result.delta is not None
        assert result.delta < Decimal("0")

    def test_gamma_non_negative(self, standard_call_input):
        """Gamma is non-negative."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_call_input)

        assert result.gamma is not None
        assert result.gamma >= Decimal("0")

    def test_vega_non_negative(self, standard_call_input):
        """Vega is non-negative for standard options."""
        pricer = QuantLibEuropeanOptionPricer()
        result = pricer.price(standard_call_input)

        assert result.vega is not None
        assert result.vega >= Decimal("0")

    def test_quantity_scales_fair_value(self, valuation_date):
        """Fair value scales with quantity."""
        input_qty_1 = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-1",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("100"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
            quantity=Decimal("1"),
        )
        input_qty_10 = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-10",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("100"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
            quantity=Decimal("10"),
        )

        pricer = QuantLibEuropeanOptionPricer()
        result_1 = pricer.price(input_qty_1)
        result_10 = pricer.price(input_qty_10)

        # Fair value should scale approximately linearly with quantity
        assert abs(
            (result_10.fair_value_base_ccy / result_1.fair_value_base_ccy) - Decimal("10")
        ) < Decimal("0.01")

    def test_quantity_scales_delta(self, valuation_date):
        """Delta scales with quantity."""
        input_qty_1 = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-1",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("100"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
            quantity=Decimal("1"),
        )
        input_qty_5 = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-5",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("100"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
            quantity=Decimal("5"),
        )

        pricer = QuantLibEuropeanOptionPricer()
        result_1 = pricer.price(input_qty_1)
        result_5 = pricer.price(input_qty_5)

        # Delta should scale with quantity
        assert abs((result_5.delta / result_1.delta) - Decimal("5")) < Decimal("0.01")

    def test_otm_call_lower_value_than_atm(self, valuation_date):
        """Out-of-the-money call worth less than at-the-money."""
        atm_input = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-ATM",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("100"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
        )
        otm_input = EuropeanEquityOptionPricingInput(
            derivative_id="CALL-OTM",
            pricing_date=valuation_date,
            option_type=OptionType.CALL,
            spot=Decimal("100"),
            strike=Decimal("110"),
            risk_free_rate=Decimal("0.05"),
            dividend_yield=Decimal("0"),
            volatility=Decimal("0.20"),
            maturity_date=valuation_date + timedelta(days=365),
        )

        pricer = QuantLibEuropeanOptionPricer()
        atm_result = pricer.price(atm_input)
        otm_result = pricer.price(otm_input)

        assert otm_result.fair_value_base_ccy < atm_result.fair_value_base_ccy

    def test_no_database_imports(self):
        """Pricer module has no database imports."""
        import inspect

        import manco_risk.risk.derivatives.quantlib_pricer as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
