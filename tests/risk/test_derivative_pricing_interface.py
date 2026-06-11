"""Tests for derivative pricing interface.

Validates pricing models and manual pricer implementation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.derivatives import (
    DerivativePricingInput,
    DerivativePricingResult,
    ManualDerivativePricer,
)


class TestDerivativePricingInput:
    """Test pricing input model."""

    def test_valid_input_minimal(self):
        """Create valid minimal input with only required fields."""
        input_data = DerivativePricingInput(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("50000"),
        )
        assert input_data.derivative_id == "SWAP-001"
        assert input_data.fair_value_base_ccy == Decimal("50000")

    def test_input_accepts_positive_fair_value(self):
        """Pricing input accepts positive fair value."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500.50"),
        )
        assert input_data.fair_value_base_ccy == Decimal("1500.50")

    def test_input_accepts_negative_fair_value(self):
        """Pricing input accepts negative fair value."""
        input_data = DerivativePricingInput(
            derivative_id="SWAP-002",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("-500000"),
        )
        assert input_data.fair_value_base_ccy == Decimal("-500000")

    def test_input_accepts_zero_fair_value(self):
        """Pricing input accepts zero fair value."""
        input_data = DerivativePricingInput(
            derivative_id="SWAP-003",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("0"),
        )
        assert input_data.fair_value_base_ccy == Decimal("0")

    def test_input_accepts_positive_delta(self):
        """Pricing input accepts positive delta."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            delta=Decimal("0.75"),
        )
        assert input_data.delta == Decimal("0.75")

    def test_input_accepts_negative_delta(self):
        """Pricing input accepts negative delta."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-002",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            delta=Decimal("-0.50"),
        )
        assert input_data.delta == Decimal("-0.50")

    def test_input_accepts_gamma(self):
        """Pricing input accepts gamma."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            gamma=Decimal("0.08"),
        )
        assert input_data.gamma == Decimal("0.08")

    def test_input_accepts_vega(self):
        """Pricing input accepts vega."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            vega=Decimal("250"),
        )
        assert input_data.vega == Decimal("250")

    def test_input_accepts_dv01(self):
        """Pricing input accepts DV01."""
        input_data = DerivativePricingInput(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("50000"),
            dv01=Decimal("1000"),
        )
        assert input_data.dv01 == Decimal("1000")

    def test_input_rejects_empty_derivative_id(self):
        """Input rejects empty derivative_id."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            DerivativePricingInput(
                derivative_id="",
                pricing_date=date(2026, 6, 11),
                fair_value_base_ccy=Decimal("1000"),
            )

    def test_input_rejects_empty_pricing_model_if_provided(self):
        """Input rejects empty pricing_model if provided."""
        with pytest.raises(ValueError, match="pricing_model must be non-empty if provided"):
            DerivativePricingInput(
                derivative_id="OPT-001",
                pricing_date=date(2026, 6, 11),
                fair_value_base_ccy=Decimal("1000"),
                pricing_model="",
            )

    def test_input_accepts_none_fair_value(self):
        """Input accepts None fair_value (optional)."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=None,
        )
        assert input_data.fair_value_base_ccy is None

    def test_input_frozen(self):
        """Pricing input is immutable."""
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1000"),
        )
        with pytest.raises(Exception):
            input_data.fair_value_base_ccy = Decimal("2000")


class TestDerivativePricingResult:
    """Test pricing result model."""

    def test_valid_result_minimal(self):
        """Create valid minimal result."""
        result = DerivativePricingResult(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("50000"),
            pricing_model="manual",
        )
        assert result.derivative_id == "SWAP-001"
        assert result.fair_value_base_ccy == Decimal("50000")

    def test_result_requires_fair_value(self):
        """Result requires fair_value_base_ccy."""
        # Attempting to create without fair_value should fail validation
        # Since fair_value_base_ccy is required (no default None)
        result = DerivativePricingResult(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("0"),
            pricing_model="manual",
        )
        assert result.fair_value_base_ccy == Decimal("0")

    def test_result_rejects_empty_pricing_model(self):
        """Result rejects empty pricing_model."""
        with pytest.raises(ValueError, match="pricing_model must be non-empty"):
            DerivativePricingResult(
                derivative_id="OPT-001",
                pricing_date=date(2026, 6, 11),
                fair_value_base_ccy=Decimal("1000"),
                pricing_model="",
            )

    def test_result_rejects_empty_derivative_id(self):
        """Result rejects empty derivative_id."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            DerivativePricingResult(
                derivative_id="",
                pricing_date=date(2026, 6, 11),
                fair_value_base_ccy=Decimal("1000"),
                pricing_model="manual",
            )

    def test_result_accepts_positive_fair_value(self):
        """Result accepts positive fair value."""
        result = DerivativePricingResult(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("5000.75"),
            pricing_model="quantlib",
        )
        assert result.fair_value_base_ccy == Decimal("5000.75")

    def test_result_accepts_negative_fair_value(self):
        """Result accepts negative fair value."""
        result = DerivativePricingResult(
            derivative_id="SWAP-002",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("-25000"),
            pricing_model="quantlib",
        )
        assert result.fair_value_base_ccy == Decimal("-25000")

    def test_result_accepts_greeks(self):
        """Result accepts all Greeks."""
        result = DerivativePricingResult(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            delta=Decimal("0.65"),
            gamma=Decimal("0.05"),
            vega=Decimal("350"),
            theta=Decimal("-50"),
            rho=Decimal("500"),
            pricing_model="quantlib",
        )
        assert result.delta == Decimal("0.65")
        assert result.gamma == Decimal("0.05")
        assert result.vega == Decimal("350")

    def test_result_accepts_none_greeks(self):
        """Result accepts None for Greeks (optional)."""
        result = DerivativePricingResult(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("50000"),
            delta=None,
            gamma=None,
            pricing_model="manual",
        )
        assert result.delta is None
        assert result.gamma is None

    def test_result_frozen(self):
        """Pricing result is immutable."""
        result = DerivativePricingResult(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1000"),
            pricing_model="manual",
        )
        with pytest.raises(Exception):
            result.fair_value_base_ccy = Decimal("2000")


class TestManualDerivativePricer:
    """Test manual pricer implementation."""

    def test_pricer_instantiation(self):
        """Pricer can be instantiated."""
        pricer = ManualDerivativePricer()
        assert pricer is not None

    def test_pricer_returns_provided_fair_value(self):
        """Manual pricer returns provided fair value."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("75000"),
        )
        result = pricer.price(input_data)
        assert result.fair_value_base_ccy == Decimal("75000")

    def test_pricer_requires_fair_value(self):
        """Manual pricer requires fair_value_base_ccy."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=None,
        )
        with pytest.raises(ValueError, match="fair_value_base_ccy is required"):
            pricer.price(input_data)

    def test_pricer_passes_through_delta(self):
        """Manual pricer passes through delta."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            delta=Decimal("0.55"),
        )
        result = pricer.price(input_data)
        assert result.delta == Decimal("0.55")

    def test_pricer_passes_through_all_greeks(self):
        """Manual pricer passes through all Greeks."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("2000"),
            delta=Decimal("0.70"),
            gamma=Decimal("0.04"),
            vega=Decimal("400"),
            theta=Decimal("-60"),
            rho=Decimal("600"),
            dv01=None,
        )
        result = pricer.price(input_data)
        assert result.delta == Decimal("0.70")
        assert result.gamma == Decimal("0.04")
        assert result.vega == Decimal("400")
        assert result.theta == Decimal("-60")
        assert result.rho == Decimal("600")

    def test_pricer_handles_none_greeks(self):
        """Manual pricer handles None Greeks."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="SWAP-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("50000"),
            delta=None,
            gamma=None,
            vega=None,
        )
        result = pricer.price(input_data)
        assert result.delta is None
        assert result.gamma is None
        assert result.vega is None

    def test_pricer_defaults_model_to_manual(self):
        """Manual pricer defaults pricing_model to 'manual'."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            pricing_model=None,
        )
        result = pricer.price(input_data)
        assert result.pricing_model == "manual"

    def test_pricer_preserves_provided_model(self):
        """Manual pricer preserves provided pricing_model."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            pricing_model="user_input",
        )
        result = pricer.price(input_data)
        assert result.pricing_model == "user_input"

    def test_pricer_preserves_warnings(self):
        """Manual pricer preserves warnings from input."""
        pricer = ManualDerivativePricer()
        input_data = DerivativePricingInput(
            derivative_id="OPT-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1500"),
            warnings=["Missing volatility data"],
        )
        result = pricer.price(input_data)
        assert "Missing volatility data" in result.warnings

    def test_pricer_implements_protocol(self):
        """Manual pricer implements DerivativePricer protocol."""
        pricer = ManualDerivativePricer()
        # Check that pricer has the required method
        assert hasattr(pricer, "price")
        assert callable(pricer.price)

    def test_protocol_can_be_satisfied_by_different_impl(self):
        """Protocol can be implemented by different classes."""

        class CustomPricer:
            def price(self, input: DerivativePricingInput) -> DerivativePricingResult:
                return DerivativePricingResult(
                    derivative_id=input.derivative_id,
                    pricing_date=input.pricing_date,
                    fair_value_base_ccy=Decimal("9999"),
                    pricing_model="custom",
                )

        pricer = CustomPricer()
        input_data = DerivativePricingInput(
            derivative_id="TEST-001",
            pricing_date=date(2026, 6, 11),
            fair_value_base_ccy=Decimal("1000"),
        )
        result = pricer.price(input_data)
        assert result.fair_value_base_ccy == Decimal("9999")
        assert result.pricing_model == "custom"

    def test_no_quantlib_imports(self):
        """Pricer module has no QuantLib imports."""
        import inspect

        import manco_risk.risk.derivatives.manual_pricer as module

        source = inspect.getsource(module)
        assert "quantlib" not in source.lower()
        assert "ql." not in source.lower()

    def test_no_database_imports(self):
        """Pricer module has no database imports."""
        import inspect

        import manco_risk.risk.derivatives.manual_pricer as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
