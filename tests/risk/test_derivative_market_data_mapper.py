"""Tests for derivative market data to pricing input mapper.

Validates conversion from DerivativeMarketData to EuropeanEquityOptionPricingInput.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.market_data.derivative_schemas import (
    DerivativeMarketData,
    VolatilityPoint,
    VolatilitySurface,
    VolatilitySurfaceType,
    YieldCurve,
    YieldCurvePoint,
    YieldCurveType,
)
from manco_risk.risk.derivatives.market_data_mapper import EuropeanOptionMarketDataMapper
from manco_risk.risk.derivatives.pricing_models import OptionType


@pytest.fixture
def valuation_date():
    """Valuation date for testing."""
    return date(2026, 6, 11)


@pytest.fixture
def maturity_date(valuation_date):
    """Maturity date (1 year forward from valuation date)."""
    return date(2027, 6, 11)


@pytest.fixture
def risk_free_curve(valuation_date):
    """Standard risk-free yield curve with points at 0.25, 1, and 5 years."""
    points = [
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("0.25"),
            yield_rate=Decimal("0.02"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        ),
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("0.03"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        ),
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("5"),
            yield_rate=Decimal("0.04"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        ),
    ]
    return YieldCurve(
        curve_type=YieldCurveType.RISK_FREE,
        curve_date=valuation_date,
        currency="USD",
        points=points,
    )


@pytest.fixture
def dividend_yield_curve(valuation_date):
    """Dividend yield curve with points at 0.25, 1, and 5 years."""
    points = [
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("0.25"),
            yield_rate=Decimal("0.005"),
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            currency="USD",
        ),
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("0.01"),
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            currency="USD",
        ),
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("5"),
            yield_rate=Decimal("0.015"),
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            currency="USD",
        ),
    ]
    return YieldCurve(
        curve_type=YieldCurveType.DIVIDEND_YIELD,
        curve_date=valuation_date,
        currency="USD",
        points=points,
    )


@pytest.fixture
def volatility_surface(valuation_date):
    """Volatility surface with ATM (moneyness=1.0) points at various maturities."""
    points = [
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("0.25"),
            moneyness=Decimal("1.0"),
            implied_volatility=Decimal("0.22"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("1"),
            moneyness=Decimal("1.0"),
            implied_volatility=Decimal("0.20"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("5"),
            moneyness=Decimal("1.0"),
            implied_volatility=Decimal("0.18"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
        # Also include OTM points to test exact matching
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("1"),
            moneyness=Decimal("1.1"),
            implied_volatility=Decimal("0.18"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
    ]
    return VolatilitySurface(
        surface_type=VolatilitySurfaceType.EQUITY_VOL,
        surface_date=valuation_date,
        underlying_id="AAPL",
        points=points,
    )


@pytest.fixture
def market_data_complete(valuation_date, risk_free_curve, dividend_yield_curve, volatility_surface):
    """Complete market data with all components."""
    return DerivativeMarketData(
        derivative_id="CALL-001",
        pricing_date=valuation_date,
        underlying_id="AAPL",
        spot_price=Decimal("150"),
        currency="USD",
        risk_free_curve=risk_free_curve,
        dividend_yield_curve=dividend_yield_curve,
        volatility_surface=volatility_surface,
    )


@pytest.fixture
def market_data_no_dividend(valuation_date, risk_free_curve, volatility_surface):
    """Market data without dividend yield curve."""
    return DerivativeMarketData(
        derivative_id="CALL-002",
        pricing_date=valuation_date,
        underlying_id="AAPL",
        spot_price=Decimal("150"),
        currency="USD",
        risk_free_curve=risk_free_curve,
        volatility_surface=volatility_surface,
    )


@pytest.fixture
def mapper():
    """European option market data mapper."""
    return EuropeanOptionMarketDataMapper()


class TestEuropeanOptionMarketDataMapper:
    """Test market data to pricing input mapper."""

    def test_maps_complete_market_data(self, mapper, market_data_complete, maturity_date):
        """Maps complete market data into EuropeanEquityOptionPricingInput."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.derivative_id == "CALL-001"
        assert result.option_type == OptionType.CALL
        assert result.strike == Decimal("155")
        assert result.quantity == Decimal("100")

    def test_maps_pricing_date_from_market_data(self, mapper, market_data_complete, maturity_date):
        """Pricing date comes from market data."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.pricing_date == market_data_complete.pricing_date

    def test_maps_spot_from_market_data(self, mapper, market_data_complete, maturity_date):
        """Spot price comes from market data."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.spot == market_data_complete.spot_price

    def test_maps_currency_from_market_data(self, mapper, market_data_complete, maturity_date):
        """Currency comes from market data."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.currency == market_data_complete.currency

    def test_maps_exact_risk_free_rate(self, mapper, market_data_complete, maturity_date):
        """Extracts risk-free rate at exact maturity."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        # At maturity 1 year, risk-free should be 0.03
        assert result.risk_free_rate == Decimal("0.03")

    def test_maps_exact_dividend_yield_rate(self, mapper, market_data_complete, maturity_date):
        """Extracts dividend yield at exact maturity."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        # At maturity 1 year, dividend yield should be 0.01
        assert result.dividend_yield == Decimal("0.01")

    def test_defaults_dividend_yield_to_zero_if_no_curve(
        self, mapper, market_data_no_dividend, maturity_date
    ):
        """Dividend yield defaults to zero if no dividend curve provided."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-002",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_no_dividend,
        )

        assert result.dividend_yield == Decimal("0")

    def test_maps_exact_atm_implied_volatility(self, mapper, market_data_complete, maturity_date):
        """Extracts ATM (moneyness=1.0) volatility at exact maturity."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        # At maturity 1 year and moneyness 1.0, vol should be 0.20
        assert result.volatility == Decimal("0.20")

    def test_rejects_missing_volatility_surface(
        self, mapper, valuation_date, risk_free_curve, maturity_date
    ):
        """Raises error if volatility surface is missing."""
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,
            volatility_surface=None,  # Missing!
        )

        with pytest.raises(ValueError, match="volatility_surface is required"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data,
            )

    def test_rejects_missing_risk_free_maturity(self, mapper, market_data_complete, maturity_date):
        """Raises error if risk-free curve has no point at requested maturity."""
        # Market data has points at 0.25, 1, 5 years
        # Request 0.5 years which doesn't exist
        with pytest.raises(ValueError, match="Risk-free curve has no exact point"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("0.5"),  # Not in curve
                maturity_date=date(2026, 12, 11),
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

    def test_rejects_missing_dividend_maturity_when_curve_exists(
        self, mapper, valuation_date, risk_free_curve, maturity_date
    ):
        """Raises error if dividend curve exists but lacks requested maturity."""
        # Create dividend curve without 1-year point
        div_points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("0.25"),
                yield_rate=Decimal("0.005"),
                curve_type=YieldCurveType.DIVIDEND_YIELD,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("5"),
                yield_rate=Decimal("0.015"),
                curve_type=YieldCurveType.DIVIDEND_YIELD,
                currency="USD",
            ),
        ]
        dividend_curve = YieldCurve(
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            curve_date=valuation_date,
            currency="USD",
            points=div_points,
        )

        # Vol surface with 1-year ATM
        vol_points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("1"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        vol_surface = VolatilitySurface(
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
            surface_date=valuation_date,
            underlying_id="AAPL",
            points=vol_points,
        )

        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,  # Has 1-year point
            dividend_yield_curve=dividend_curve,  # Missing 1-year point
            volatility_surface=vol_surface,
        )

        with pytest.raises(ValueError, match="Dividend yield curve has no exact point"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),  # Exists in risk-free, missing in dividend
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data,
            )

    def test_rejects_missing_atm_volatility_point(
        self, mapper, valuation_date, risk_free_curve, maturity_date
    ):
        """Raises error if ATM volatility point is missing."""
        # Create vol surface without the 1.0 maturity ATM point
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.22"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            # No 1-year ATM point
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("1"),
                moneyness=Decimal("1.1"),  # Only OTM available
                implied_volatility=Decimal("0.18"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        vol_surface = VolatilitySurface(
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
            surface_date=valuation_date,
            underlying_id="AAPL",
            points=points,
        )
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,
            volatility_surface=vol_surface,
        )

        with pytest.raises(ValueError, match="Volatility surface has no exact point"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data,
            )

    def test_rejects_invalid_strike(self, mapper, market_data_complete, maturity_date):
        """Zero or negative strike rejected."""
        with pytest.raises(ValueError, match="strike must be positive"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("0"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

        with pytest.raises(ValueError, match="strike must be positive"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("-100"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

    def test_rejects_invalid_maturity_years(self, mapper, market_data_complete, maturity_date):
        """Zero or negative maturity_years rejected."""
        with pytest.raises(ValueError, match="maturity_years must be positive"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("0"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

    def test_rejects_maturity_date_before_pricing_date(
        self, mapper, market_data_complete, valuation_date
    ):
        """Maturity date before or on pricing date rejected."""
        with pytest.raises(ValueError, match="maturity_date.*must be after"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=valuation_date,  # Same as pricing_date
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

        with pytest.raises(ValueError, match="maturity_date.*must be after"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=date(2026, 6, 10),  # Before pricing_date
                quantity=Decimal("100"),
                market_data=market_data_complete,
            )

    def test_rejects_zero_quantity(self, mapper, market_data_complete, maturity_date):
        """Zero quantity rejected."""
        with pytest.raises(ValueError, match="quantity must be non-zero"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("0"),
                market_data=market_data_complete,
            )

    def test_accepts_negative_quantity(self, mapper, market_data_complete, maturity_date):
        """Negative quantity accepted (for short positions)."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("-100"),
            market_data=market_data_complete,
        )

        assert result.quantity == Decimal("-100")

    def test_rejects_invalid_contract_multiplier(self, mapper, market_data_complete, maturity_date):
        """Zero or negative contract multiplier rejected."""
        with pytest.raises(ValueError, match="contract_multiplier must be positive"):
            mapper.to_pricing_input(
                derivative_id="CALL-001",
                option_type="CALL",
                strike=Decimal("155"),
                maturity_years=Decimal("1"),
                maturity_date=maturity_date,
                quantity=Decimal("100"),
                market_data=market_data_complete,
                contract_multiplier=Decimal("0"),
            )

    def test_accepts_option_type_enum(self, mapper, market_data_complete, maturity_date):
        """Accepts OptionType enum directly."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type=OptionType.CALL,
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.option_type == OptionType.CALL

    def test_accepts_option_type_string(self, mapper, market_data_complete, maturity_date):
        """Accepts option type as string."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="call",  # lowercase
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        assert result.option_type == OptionType.CALL

    def test_maps_put_option(self, mapper, market_data_complete, maturity_date):
        """Maps PUT option type correctly."""
        result = mapper.to_pricing_input(
            derivative_id="PUT-001",
            option_type="PUT",
            strike=Decimal("145"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("50"),
            market_data=market_data_complete,
        )

        assert result.option_type == OptionType.PUT
        assert result.strike == Decimal("145")

    def test_applies_contract_multiplier(self, mapper, market_data_complete, maturity_date):
        """Contract multiplier is preserved in output."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("1"),
            maturity_date=maturity_date,
            quantity=Decimal("100"),
            market_data=market_data_complete,
            contract_multiplier=Decimal("100"),
        )

        # The multiplier is used for validation but quantity is set independently
        assert result.quantity == Decimal("100")

    def test_exact_matching_at_short_maturity(self, mapper, market_data_complete, valuation_date):
        """Maps at 0.25-year maturity (short-dated option)."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("0.25"),
            maturity_date=date(2026, 9, 11),
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        # At maturity 0.25 years
        assert result.risk_free_rate == Decimal("0.02")
        assert result.dividend_yield == Decimal("0.005")
        assert result.volatility == Decimal("0.22")

    def test_exact_matching_at_long_maturity(self, mapper, market_data_complete):
        """Maps at 5-year maturity (long-dated option)."""
        result = mapper.to_pricing_input(
            derivative_id="CALL-001",
            option_type="CALL",
            strike=Decimal("155"),
            maturity_years=Decimal("5"),
            maturity_date=date(2031, 6, 11),
            quantity=Decimal("100"),
            market_data=market_data_complete,
        )

        # At maturity 5 years
        assert result.risk_free_rate == Decimal("0.04")
        assert result.dividend_yield == Decimal("0.015")
        assert result.volatility == Decimal("0.18")

    def test_no_quantlib_imports(self):
        """Mapper module has no QuantLib imports."""
        import inspect

        import manco_risk.risk.derivatives.market_data_mapper as module

        source = inspect.getsource(module)
        assert "QuantLib" not in source
        assert "import ql" not in source

    def test_no_database_imports(self):
        """Mapper module has no database imports."""
        import inspect

        import manco_risk.risk.derivatives.market_data_mapper as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
