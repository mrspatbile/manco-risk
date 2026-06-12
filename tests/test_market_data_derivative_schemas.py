"""Tests for derivative market data schemas.

Validates yield curve, volatility surface, and derivative market data models
including all validation rules and constraints.
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


@pytest.fixture
def valuation_date():
    """Valuation date for testing."""
    return date(2026, 6, 11)


@pytest.fixture
def risk_free_point(valuation_date):
    """Standard risk-free curve point."""
    return YieldCurvePoint(
        curve_date=valuation_date,
        maturity_years=Decimal("1"),
        yield_rate=Decimal("0.03"),
        curve_type=YieldCurveType.RISK_FREE,
        currency="USD",
    )


@pytest.fixture
def risk_free_curve(valuation_date, risk_free_point):
    """Standard risk-free yield curve."""
    points = [
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("0.25"),
            yield_rate=Decimal("0.02"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        ),
        risk_free_point,
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
    """Standard dividend yield curve."""
    points = [
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("0.5"),
            yield_rate=Decimal("0.01"),
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            currency="USD",
        ),
        YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("2"),
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
def volatility_point(valuation_date):
    """Standard volatility surface point."""
    return VolatilityPoint(
        surface_date=valuation_date,
        underlying_id="AAPL",
        maturity_years=Decimal("0.25"),
        moneyness=Decimal("1.0"),
        implied_volatility=Decimal("0.20"),
        surface_type=VolatilitySurfaceType.EQUITY_VOL,
    )


@pytest.fixture
def volatility_surface(valuation_date):
    """Standard volatility surface."""
    points = [
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("0.25"),
            moneyness=Decimal("0.95"),
            implied_volatility=Decimal("0.22"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("0.25"),
            moneyness=Decimal("1.0"),
            implied_volatility=Decimal("0.20"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        ),
        VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("0.25"),
            moneyness=Decimal("1.05"),
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


class TestYieldCurvePoint:
    """Test YieldCurvePoint model."""

    def test_valid_point(self, valuation_date):
        """Create valid yield curve point."""
        point = YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("0.03"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        )
        assert point.maturity_years == Decimal("1")
        assert point.yield_rate == Decimal("0.03")

    def test_rejects_zero_maturity(self, valuation_date):
        """Zero maturity rejected."""
        with pytest.raises(ValueError, match="maturity_years must be positive"):
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("0"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            )

    def test_rejects_negative_maturity(self, valuation_date):
        """Negative maturity rejected."""
        with pytest.raises(ValueError, match="maturity_years must be positive"):
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("-1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            )

    def test_allows_negative_yield_rate(self, valuation_date):
        """Negative yield rate allowed (e.g., EUR, JPY)."""
        point = YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("-0.005"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="EUR",
        )
        assert point.yield_rate == Decimal("-0.005")

    def test_rejects_empty_currency(self, valuation_date):
        """Empty currency rejected."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="",
            )

    def test_accepts_optional_source(self, valuation_date):
        """Source field is optional."""
        point = YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("0.03"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
            source="Bloomberg",
        )
        assert point.source == "Bloomberg"

    def test_rejects_empty_source_if_provided(self, valuation_date):
        """Empty source rejected if provided."""
        with pytest.raises(ValueError, match="source must be non-empty if provided"):
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
                source="",
            )

    def test_frozen_model(self, valuation_date):
        """Yield curve point is immutable."""
        point = YieldCurvePoint(
            curve_date=valuation_date,
            maturity_years=Decimal("1"),
            yield_rate=Decimal("0.03"),
            curve_type=YieldCurveType.RISK_FREE,
            currency="USD",
        )
        with pytest.raises(Exception):
            point.yield_rate = Decimal("0.04")


class TestYieldCurve:
    """Test YieldCurve model."""

    def test_valid_curve(self, risk_free_curve):
        """Create valid yield curve."""
        assert len(risk_free_curve.points) == 3
        assert risk_free_curve.curve_type == YieldCurveType.RISK_FREE

    def test_rejects_empty_points(self, valuation_date):
        """Empty points list rejected."""
        with pytest.raises(ValueError, match="points must be non-empty"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=[],
            )

    def test_rejects_empty_currency(self, valuation_date, risk_free_point):
        """Empty currency rejected."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="",
                points=[risk_free_point],
            )

    def test_rejects_mixed_curve_types(self, valuation_date):
        """Mixed curve types rejected."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("2"),
                yield_rate=Decimal("0.02"),
                curve_type=YieldCurveType.DIVIDEND_YIELD,  # different type
                currency="USD",
            ),
        ]
        with pytest.raises(ValueError, match="all points must have curve_type"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=points,
            )

    def test_rejects_mixed_dates(self, valuation_date):
        """Mixed curve dates rejected."""
        other_date = date(2026, 6, 12)
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=other_date,  # different date
                maturity_years=Decimal("2"),
                yield_rate=Decimal("0.02"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
        ]
        with pytest.raises(ValueError, match="all points must have curve_date"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=points,
            )

    def test_rejects_mixed_currencies(self, valuation_date):
        """Mixed currencies rejected."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("2"),
                yield_rate=Decimal("0.02"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="EUR",  # different currency
            ),
        ]
        with pytest.raises(ValueError, match="all points must have currency"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=points,
            )

    def test_rejects_duplicate_maturities(self, valuation_date):
        """Duplicate maturities rejected."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),  # duplicate maturity
                yield_rate=Decimal("0.032"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
        ]
        with pytest.raises(ValueError, match="maturities must be strictly increasing"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=points,
            )

    def test_rejects_non_increasing_maturities(self, valuation_date):
        """Non-increasing maturities rejected."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("2"),
                yield_rate=Decimal("0.04"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),  # out of order
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
        ]
        with pytest.raises(ValueError, match="maturities must be strictly increasing"):
            YieldCurve(
                curve_type=YieldCurveType.RISK_FREE,
                curve_date=valuation_date,
                currency="USD",
                points=points,
            )

    def test_frozen_model(self, risk_free_curve):
        """Yield curve is immutable."""
        with pytest.raises(Exception):
            risk_free_curve.points = []


class TestVolatilityPoint:
    """Test VolatilityPoint model."""

    def test_valid_point(self, valuation_date):
        """Create valid volatility point."""
        point = VolatilityPoint(
            surface_date=valuation_date,
            underlying_id="AAPL",
            maturity_years=Decimal("0.25"),
            moneyness=Decimal("1.0"),
            implied_volatility=Decimal("0.20"),
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
        )
        assert point.maturity_years == Decimal("0.25")

    def test_rejects_empty_underlying_id(self, valuation_date):
        """Empty underlying ID rejected."""
        with pytest.raises(ValueError, match="underlying_id must be non-empty"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_zero_maturity(self, valuation_date):
        """Zero maturity rejected."""
        with pytest.raises(ValueError, match="maturity_years must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_negative_maturity(self, valuation_date):
        """Negative maturity rejected."""
        with pytest.raises(ValueError, match="maturity_years must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("-0.1"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_zero_moneyness(self, valuation_date):
        """Zero moneyness rejected."""
        with pytest.raises(ValueError, match="moneyness must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_negative_moneyness(self, valuation_date):
        """Negative moneyness rejected."""
        with pytest.raises(ValueError, match="moneyness must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("-0.5"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_zero_volatility(self, valuation_date):
        """Zero volatility rejected."""
        with pytest.raises(ValueError, match="implied_volatility must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_rejects_negative_volatility(self, valuation_date):
        """Negative volatility rejected."""
        with pytest.raises(ValueError, match="implied_volatility must be positive"):
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("-0.1"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            )

    def test_frozen_model(self, volatility_point):
        """Volatility point is immutable."""
        with pytest.raises(Exception):
            volatility_point.implied_volatility = Decimal("0.25")


class TestVolatilitySurface:
    """Test VolatilitySurface model."""

    def test_valid_surface(self, volatility_surface):
        """Create valid volatility surface."""
        assert len(volatility_surface.points) == 3
        assert volatility_surface.surface_type == VolatilitySurfaceType.EQUITY_VOL

    def test_rejects_empty_points(self, valuation_date):
        """Empty points list rejected."""
        with pytest.raises(ValueError, match="points must be non-empty"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="AAPL",
                points=[],
            )

    def test_rejects_empty_underlying_id(self, valuation_date, volatility_point):
        """Empty underlying ID rejected."""
        with pytest.raises(ValueError, match="underlying_id must be non-empty"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="",
                points=[volatility_point],
            )

    def test_rejects_mixed_surface_types(self, valuation_date):
        """Mixed surface types rejected."""
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.5"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.18"),
                surface_type=VolatilitySurfaceType.FX_VOL,  # different type
            ),
        ]
        with pytest.raises(ValueError, match="all points must have surface_type"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="AAPL",
                points=points,
            )

    def test_rejects_mixed_dates(self, valuation_date):
        """Mixed surface dates rejected."""
        other_date = date(2026, 6, 12)
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            VolatilityPoint(
                surface_date=other_date,  # different date
                underlying_id="AAPL",
                maturity_years=Decimal("0.5"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.18"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        with pytest.raises(ValueError, match="all points must have surface_date"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="AAPL",
                points=points,
            )

    def test_rejects_mixed_underlyings(self, valuation_date):
        """Mixed underlyings rejected."""
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="MSFT",  # different underlying
                maturity_years=Decimal("0.5"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.18"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        with pytest.raises(ValueError, match="all points must have underlying_id"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="AAPL",
                points=points,
            )

    def test_rejects_duplicate_grid_points(self, valuation_date):
        """Duplicate (maturity, moneyness) pairs rejected."""
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),  # duplicate grid point
                implied_volatility=Decimal("0.21"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        with pytest.raises(ValueError, match="duplicate grid point"):
            VolatilitySurface(
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
                surface_date=valuation_date,
                underlying_id="AAPL",
                points=points,
            )

    def test_allows_unsorted_points(self, valuation_date):
        """Unsorted points allowed (no sort enforcement)."""
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.5"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.18"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        surface = VolatilitySurface(
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
            surface_date=valuation_date,
            underlying_id="AAPL",
            points=points,
        )
        assert len(surface.points) == 2

    def test_frozen_model(self, volatility_surface):
        """Volatility surface is immutable."""
        with pytest.raises(Exception):
            volatility_surface.points = []


class TestDerivativeMarketData:
    """Test DerivativeMarketData model."""

    def test_valid_bundle(self, valuation_date, risk_free_curve, volatility_surface):
        """Create valid derivative market data bundle."""
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,
            volatility_surface=volatility_surface,
        )
        assert market_data.derivative_id == "CALL-001"

    def test_valid_bundle_with_dividend_yield(
        self, valuation_date, risk_free_curve, dividend_yield_curve, volatility_surface
    ):
        """Create valid bundle with dividend yield curve."""
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,
            dividend_yield_curve=dividend_yield_curve,
            volatility_surface=volatility_surface,
        )
        assert market_data.dividend_yield_curve is not None

    def test_rejects_empty_derivative_id(self, valuation_date, risk_free_curve):
        """Empty derivative_id rejected."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            DerivativeMarketData(
                derivative_id="",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
            )

    def test_rejects_empty_underlying_id(self, valuation_date, risk_free_curve):
        """Empty underlying_id rejected."""
        with pytest.raises(ValueError, match="underlying_id must be non-empty"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
            )

    def test_rejects_zero_spot_price(self, valuation_date, risk_free_curve):
        """Zero spot price rejected."""
        with pytest.raises(ValueError, match="spot_price must be positive"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("0"),
                currency="USD",
                risk_free_curve=risk_free_curve,
            )

    def test_rejects_negative_spot_price(self, valuation_date, risk_free_curve):
        """Negative spot price rejected."""
        with pytest.raises(ValueError, match="spot_price must be positive"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("-100"),
                currency="USD",
                risk_free_curve=risk_free_curve,
            )

    def test_rejects_empty_currency(self, valuation_date, risk_free_curve):
        """Empty currency rejected."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="",
                risk_free_curve=risk_free_curve,
            )

    def test_rejects_non_risk_free_curve(self, valuation_date, dividend_yield_curve):
        """Non-risk-free curve rejected as risk_free_curve."""
        with pytest.raises(ValueError, match="risk_free_curve must have type RISK_FREE"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=dividend_yield_curve,
            )

    def test_rejects_wrong_risk_free_date(self, valuation_date, risk_free_curve):
        """Risk-free curve with wrong date rejected."""
        other_date = date(2026, 6, 12)
        points = [
            YieldCurvePoint(
                curve_date=other_date,  # wrong date
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="USD",
            ),
        ]
        wrong_curve = YieldCurve(
            curve_type=YieldCurveType.RISK_FREE,
            curve_date=other_date,
            currency="USD",
            points=points,
        )
        with pytest.raises(ValueError, match="risk_free_curve date.*must equal"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=wrong_curve,
            )

    def test_rejects_wrong_risk_free_currency(self, valuation_date):
        """Risk-free curve with wrong currency rejected."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.03"),
                curve_type=YieldCurveType.RISK_FREE,
                currency="EUR",  # wrong currency
            ),
        ]
        wrong_curve = YieldCurve(
            curve_type=YieldCurveType.RISK_FREE,
            curve_date=valuation_date,
            currency="EUR",
            points=points,
        )
        with pytest.raises(ValueError, match="risk_free_curve currency.*must equal"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=wrong_curve,
            )

    def test_rejects_wrong_dividend_curve_type(self, valuation_date, risk_free_curve):
        """Non-dividend-yield curve rejected as dividend_yield_curve."""
        points = [
            YieldCurvePoint(
                curve_date=valuation_date,
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.01"),
                curve_type=YieldCurveType.RISK_FREE,  # wrong type
                currency="USD",
            ),
        ]
        wrong_curve = YieldCurve(
            curve_type=YieldCurveType.RISK_FREE,
            curve_date=valuation_date,
            currency="USD",
            points=points,
        )
        with pytest.raises(ValueError, match="dividend_yield_curve must have type"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
                dividend_yield_curve=wrong_curve,
            )

    def test_rejects_wrong_dividend_date(self, valuation_date, risk_free_curve):
        """Dividend curve with wrong date rejected."""
        other_date = date(2026, 6, 12)
        points = [
            YieldCurvePoint(
                curve_date=other_date,  # wrong date
                maturity_years=Decimal("1"),
                yield_rate=Decimal("0.01"),
                curve_type=YieldCurveType.DIVIDEND_YIELD,
                currency="USD",
            ),
        ]
        wrong_curve = YieldCurve(
            curve_type=YieldCurveType.DIVIDEND_YIELD,
            curve_date=other_date,
            currency="USD",
            points=points,
        )
        with pytest.raises(ValueError, match="dividend_yield_curve date.*must equal"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
                dividend_yield_curve=wrong_curve,
            )

    def test_rejects_wrong_volatility_date(self, valuation_date, risk_free_curve):
        """Volatility surface with wrong date rejected."""
        other_date = date(2026, 6, 12)
        points = [
            VolatilityPoint(
                surface_date=other_date,  # wrong date
                underlying_id="AAPL",
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        wrong_surface = VolatilitySurface(
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
            surface_date=other_date,
            underlying_id="AAPL",
            points=points,
        )
        with pytest.raises(ValueError, match="volatility_surface date.*must equal"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
                volatility_surface=wrong_surface,
            )

    def test_rejects_wrong_volatility_underlying(self, valuation_date, risk_free_curve):
        """Volatility surface with wrong underlying rejected."""
        points = [
            VolatilityPoint(
                surface_date=valuation_date,
                underlying_id="MSFT",  # wrong underlying
                maturity_years=Decimal("0.25"),
                moneyness=Decimal("1.0"),
                implied_volatility=Decimal("0.20"),
                surface_type=VolatilitySurfaceType.EQUITY_VOL,
            ),
        ]
        wrong_surface = VolatilitySurface(
            surface_type=VolatilitySurfaceType.EQUITY_VOL,
            surface_date=valuation_date,
            underlying_id="MSFT",
            points=points,
        )
        with pytest.raises(ValueError, match="volatility_surface underlying_id.*must equal"):
            DerivativeMarketData(
                derivative_id="CALL-001",
                pricing_date=valuation_date,
                underlying_id="AAPL",
                spot_price=Decimal("150"),
                currency="USD",
                risk_free_curve=risk_free_curve,
                volatility_surface=wrong_surface,
            )

    def test_serialization(
        self, valuation_date, risk_free_curve, dividend_yield_curve, volatility_surface
    ):
        """Complete market data bundle can be serialized."""
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150.50"),
            currency="USD",
            risk_free_curve=risk_free_curve,
            dividend_yield_curve=dividend_yield_curve,
            volatility_surface=volatility_surface,
            source="Bloomberg",
        )
        dumped = market_data.model_dump()
        assert dumped["derivative_id"] == "CALL-001"
        assert dumped["spot_price"] == Decimal("150.50")
        assert "risk_free_curve" in dumped
        assert "dividend_yield_curve" in dumped
        assert "volatility_surface" in dumped

    def test_frozen_model(self, valuation_date, risk_free_curve):
        """Derivative market data is immutable."""
        market_data = DerivativeMarketData(
            derivative_id="CALL-001",
            pricing_date=valuation_date,
            underlying_id="AAPL",
            spot_price=Decimal("150"),
            currency="USD",
            risk_free_curve=risk_free_curve,
        )
        with pytest.raises(Exception):
            market_data.spot_price = Decimal("155")

    def test_no_quantlib_imports(self):
        """Derivative schemas module has no QuantLib imports."""
        import inspect

        import manco_risk.market_data.derivative_schemas as module

        source = inspect.getsource(module)
        assert "QuantLib" not in source
        assert "import ql" not in source

    def test_no_database_imports(self):
        """Derivative schemas module has no database imports."""
        import inspect

        import manco_risk.market_data.derivative_schemas as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
