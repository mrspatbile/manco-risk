"""Tests for option exposure conversion.

Validates conversion of pricing results (fair value, Greeks, delta) into
derivative exposure records compatible with the derivative exposure engine.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.derivatives.exposure_conversion_models import (
    OptionExposureConversionInput,
)
from manco_risk.risk.derivatives.exposure_converter import OptionDeltaExposureConverter
from manco_risk.risk.derivatives.pricing_models import (
    DerivativePricingResult,
)
from manco_risk.risk.leverage.derivative_models import (
    DerivativeExposureSource,
    DerivativePayoffType,
    DerivativeType,
    DerivativeValuationSource,
)


@pytest.fixture
def valuation_date():
    """Valuation date for testing."""
    return date(2026, 6, 11)


@pytest.fixture
def standard_call_pricing_result(valuation_date):
    """Standard ATM call pricing result with delta."""
    return DerivativePricingResult(
        derivative_id="CALL-001",
        pricing_date=valuation_date,
        fair_value_base_ccy=Decimal("5000"),
        delta=Decimal("0.65"),
        gamma=Decimal("0.03"),
        vega=Decimal("200"),
        theta=Decimal("-50"),
        rho=Decimal("500"),
        pricing_model="QuantLib Black-Scholes-Merton",
    )


@pytest.fixture
def standard_put_pricing_result(valuation_date):
    """Standard ATM put pricing result with negative delta."""
    return DerivativePricingResult(
        derivative_id="PUT-001",
        pricing_date=valuation_date,
        fair_value_base_ccy=Decimal("4000"),
        delta=Decimal("-0.35"),
        gamma=Decimal("0.03"),
        vega=Decimal("200"),
        theta=Decimal("-50"),
        rho=Decimal("-500"),
        pricing_model="QuantLib Black-Scholes-Merton",
    )


@pytest.fixture
def converter():
    """Option delta exposure converter."""
    return OptionDeltaExposureConverter()


class TestOptionExposureConversionInput:
    """Test input model validation."""

    def test_valid_input_minimal(self, standard_call_pricing_result):
        """Create valid minimal input."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        assert input_data.derivative_id == "CALL-001"
        assert input_data.underlying_spot == Decimal("100")

    def test_input_accepts_optional_fields(self, standard_call_pricing_result):
        """Input accepts optional identifier and description."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_identifier="MSFT",
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            contract_multiplier=Decimal("100"),
            currency="USD",
            description="Microsoft CALL option",
        )
        assert input_data.underlying_identifier == "MSFT"
        assert input_data.contract_multiplier == Decimal("100")

    def test_input_rejects_empty_derivative_id(self, standard_call_pricing_result):
        """Empty derivative_id rejected."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            OptionExposureConversionInput(
                derivative_id="",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("100"),
                quantity=Decimal("10"),
                currency="USD",
            )

    def test_input_rejects_zero_underlying_spot(self, standard_call_pricing_result):
        """Zero underlying spot rejected."""
        with pytest.raises(ValueError, match="underlying_spot must be positive"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("0"),
                quantity=Decimal("10"),
                currency="USD",
            )

    def test_input_rejects_negative_underlying_spot(self, standard_call_pricing_result):
        """Negative underlying spot rejected."""
        with pytest.raises(ValueError, match="underlying_spot must be positive"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("-50"),
                quantity=Decimal("10"),
                currency="USD",
            )

    def test_input_rejects_zero_quantity(self, standard_call_pricing_result):
        """Zero quantity rejected."""
        with pytest.raises(ValueError, match="quantity must be non-zero"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("100"),
                quantity=Decimal("0"),
                currency="USD",
            )

    def test_input_accepts_negative_quantity(self, standard_call_pricing_result):
        """Negative quantity accepted (for short positions)."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("-10"),
            currency="USD",
        )
        assert input_data.quantity == Decimal("-10")

    def test_input_rejects_zero_contract_multiplier(self, standard_call_pricing_result):
        """Zero contract multiplier rejected."""
        with pytest.raises(ValueError, match="contract_multiplier must be positive"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("100"),
                quantity=Decimal("10"),
                contract_multiplier=Decimal("0"),
                currency="USD",
            )

    def test_input_rejects_empty_currency(self, standard_call_pricing_result):
        """Empty currency rejected."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_spot=Decimal("100"),
                quantity=Decimal("10"),
                currency="",
            )

    def test_input_rejects_empty_underlying_identifier(self, standard_call_pricing_result):
        """Empty underlying identifier rejected if provided."""
        with pytest.raises(ValueError, match="underlying_identifier must be non-empty if provided"):
            OptionExposureConversionInput(
                derivative_id="CALL-001",
                pricing_result=standard_call_pricing_result,
                underlying_identifier="",
                underlying_spot=Decimal("100"),
                quantity=Decimal("10"),
                currency="USD",
            )


class TestOptionDeltaExposureConverter:
    """Test option delta exposure converter."""

    def test_converter_instantiation(self, converter):
        """Converter can be instantiated."""
        assert converter is not None

    def test_converts_call_delta_to_exposure(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Converts positive call delta into delta-adjusted exposure."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        # delta = 0.65, spot = 100, quantity = 10, multiplier = 1
        # exposure = 0.65 * 100 * 10 * 1 = 650
        expected_exposure = Decimal("650")
        assert result.delta_adjusted_exposure_base_ccy == expected_exposure

    def test_converts_put_delta_using_absolute_value(
        self, converter, standard_put_pricing_result, valuation_date
    ):
        """Converts negative put delta using absolute value."""
        input_data = OptionExposureConversionInput(
            derivative_id="PUT-001",
            pricing_result=standard_put_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        # delta = -0.35 (negative for put), spot = 100, quantity = 10, multiplier = 1
        # exposure = abs(-0.35) * 100 * 10 * 1 = 350
        expected_exposure = Decimal("350")
        assert result.delta_adjusted_exposure_base_ccy == expected_exposure

    def test_quantity_scales_exposure(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Quantity scales exposure."""
        input_qty_10 = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        input_qty_20 = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("20"),
            currency="USD",
        )

        result_10 = converter.convert(input_qty_10)
        result_20 = converter.convert(input_qty_20)

        # exposure should double when quantity doubles
        assert (
            result_20.delta_adjusted_exposure_base_ccy
            == result_10.delta_adjusted_exposure_base_ccy * Decimal("2")
        )

    def test_contract_multiplier_scales_exposure(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Contract multiplier scales exposure."""
        input_mult_1 = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            contract_multiplier=Decimal("1"),
            currency="USD",
        )
        input_mult_100 = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            contract_multiplier=Decimal("100"),
            currency="USD",
        )

        result_1 = converter.convert(input_mult_1)
        result_100 = converter.convert(input_mult_100)

        # exposure should scale by multiplier
        assert (
            result_100.delta_adjusted_exposure_base_ccy
            == result_1.delta_adjusted_exposure_base_ccy * Decimal("100")
        )

    def test_negative_quantity_produces_positive_exposure(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Negative quantity (short position) still produces positive exposure."""
        input_long = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        input_short = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("-10"),
            currency="USD",
        )

        result_long = converter.convert(input_long)
        result_short = converter.convert(input_short)

        # Exposure should have same magnitude regardless of position direction
        assert result_long.delta_adjusted_exposure_base_ccy == Decimal("650")
        assert result_short.delta_adjusted_exposure_base_ccy == Decimal("650")

    def test_fair_value_copied_to_result(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Fair value copied from pricing result to conversion result."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.fair_value_base_ccy == standard_call_pricing_result.fair_value_base_ccy
        assert result.fair_value_base_ccy == Decimal("5000")

    def test_fair_value_not_used_as_exposure(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Fair value is not used as exposure (they are independent)."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        # Fair value is 5000, but exposure should be delta-adjusted, not fair value
        assert result.fair_value_base_ccy == Decimal("5000")
        assert result.delta_adjusted_exposure_base_ccy == Decimal("650")
        assert result.fair_value_base_ccy != result.delta_adjusted_exposure_base_ccy

    def test_pricing_model_copied_to_valuation(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Pricing model copied from pricing result to derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.valuation.pricing_model == "QuantLib Black-Scholes-Merton"

    def test_pricing_date_copied_to_valuation(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Pricing date copied from pricing result to derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.valuation.valuation_date == valuation_date

    def test_derivative_record_type_is_option(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Derivative record has type OPTION."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.derivative_type == DerivativeType.OPTION

    def test_derivative_record_payoff_type_is_non_linear(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Derivative record has payoff type NON_LINEAR."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.payoff_type == DerivativePayoffType.NON_LINEAR

    def test_exposure_source_is_provided_delta_adjusted(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Exposure source is PROVIDED_DELTA_ADJUSTED."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert (
            result.derivative_record.exposure.exposure_source
            == DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED
        )

    def test_valuation_source_is_provided_model_value(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Valuation source is PROVIDED_MODEL_VALUE."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert (
            result.derivative_record.valuation.valuation_source
            == DerivativeValuationSource.PROVIDED_MODEL_VALUE
        )

    def test_rejects_missing_delta(self, converter, valuation_date):
        """Conversion fails clearly when delta is None."""
        pricing_result_no_delta = DerivativePricingResult(
            derivative_id="SWAP-001",
            pricing_date=valuation_date,
            fair_value_base_ccy=Decimal("50000"),
            pricing_model="swap_model",
        )

        input_data = OptionExposureConversionInput(
            derivative_id="SWAP-001",
            pricing_result=pricing_result_no_delta,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )

        with pytest.raises(ValueError, match="Delta is required for delta-adjusted exposure"):
            converter.convert(input_data)

    def test_preserves_derivative_id(self, converter, standard_call_pricing_result, valuation_date):
        """Derivative ID preserved in derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="MY-CALL-123",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.derivative_id == "MY-CALL-123"

    def test_preserves_underlying_identifier(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Underlying identifier preserved in derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_identifier="MSFT",
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.underlying_identifier == "MSFT"

    def test_preserves_currency(self, converter, standard_call_pricing_result, valuation_date):
        """Currency preserved in derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="EUR",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.currency == "EUR"

    def test_preserves_description(self, converter, standard_call_pricing_result, valuation_date):
        """Description preserved in derivative record."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
            description="Microsoft ATM call option",
        )
        result = converter.convert(input_data)

        assert result.derivative_record.description == "Microsoft ATM call option"

    def test_preserves_pricing_result_warnings(self, converter, valuation_date):
        """Pricing result warnings preserved in conversion result."""
        pricing_result_with_warnings = DerivativePricingResult(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            fair_value_base_ccy=Decimal("5000"),
            delta=Decimal("0.65"),
            pricing_model="QuantLib",
            warnings=["Volatility surface extrapolated beyond 2y"],
        )

        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=pricing_result_with_warnings,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        assert len(result.warnings) == 1
        assert result.warnings[0] == "Volatility surface extrapolated beyond 2y"

    def test_output_can_be_consumed_by_derivative_exposure_engine(
        self, converter, standard_call_pricing_result, valuation_date
    ):
        """Output is compatible with existing derivative exposure engine."""
        input_data = OptionExposureConversionInput(
            derivative_id="CALL-001",
            pricing_result=standard_call_pricing_result,
            underlying_spot=Decimal("100"),
            quantity=Decimal("10"),
            currency="USD",
        )
        result = converter.convert(input_data)

        # Result should have a DerivativeRecord that can be consumed by
        # the DerivativeExposureEngine
        record = result.derivative_record
        assert record.derivative_type is not None
        assert record.payoff_type is not None
        assert record.currency is not None
        assert record.valuation is not None
        assert record.exposure is not None
        assert record.exposure.delta_adjusted_exposure_base_ccy is not None

    def test_no_quantlib_imports(self):
        """Converter module has no QuantLib imports."""
        import inspect

        import manco_risk.risk.derivatives.exposure_converter as module

        source = inspect.getsource(module)
        assert "QuantLib" not in source
        assert "import ql" not in source

    def test_no_database_imports(self):
        """Converter module has no database imports."""
        import inspect

        import manco_risk.risk.derivatives.exposure_converter as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
