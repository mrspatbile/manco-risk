"""Tests for market data schemas."""

from datetime import date
from decimal import Decimal

from manco_risk.common import AssetClass
from manco_risk.market_data import FXRate, InstrumentInfo, Price, PriceHistory


class TestPrice:
    """Tests for Price schema."""

    def test_price_creation_valid(self) -> None:
        price = Price(
            security_id="SPY US Equity",
            date=date(2026, 6, 10),
            price=Decimal("580.50"),
            currency="USD",
        )
        assert price.security_id == "SPY US Equity"
        assert price.price == Decimal("580.50")

    def test_price_accepts_string_decimal(self) -> None:
        price = Price(
            security_id="SPY US Equity",
            date=date(2026, 6, 10),
            price="580.50",
            currency="USD",
        )
        assert isinstance(price.price, Decimal)

    def test_price_accepts_float(self) -> None:
        price = Price(
            security_id="SPY US Equity",
            date=date(2026, 6, 10),
            price=580.50,
            currency="USD",
        )
        assert isinstance(price.price, Decimal)


class TestPriceHistory:
    """Tests for PriceHistory schema."""

    def test_price_history_sorting(self) -> None:
        prices = [
            Price(
                security_id="SPY US Equity",
                date=date(2026, 6, 10),
                price=Decimal("580"),
                currency="USD",
            ),
            Price(
                security_id="SPY US Equity",
                date=date(2026, 6, 9),
                price=Decimal("579"),
                currency="USD",
            ),
            Price(
                security_id="SPY US Equity",
                date=date(2026, 6, 8),
                price=Decimal("578"),
                currency="USD",
            ),
        ]

        history = PriceHistory(security_id="SPY US Equity", prices=prices)

        assert history.prices[0].date == date(2026, 6, 8)
        assert history.prices[1].date == date(2026, 6, 9)
        assert history.prices[2].date == date(2026, 6, 10)

    def test_price_history_empty_list(self) -> None:
        history = PriceHistory(security_id="SPY US Equity", prices=[])
        assert len(history.prices) == 0


class TestInstrumentInfo:
    """Tests for InstrumentInfo schema."""

    def test_equity_info_creation(self) -> None:
        info = InstrumentInfo(
            security_id="AAPL US Equity",
            name="Apple Inc",
            asset_class=AssetClass.EQUITY,
            currency="USD",
            beta=Decimal("1.05"),
        )
        assert info.security_id == "AAPL US Equity"
        assert info.asset_class == AssetClass.EQUITY
        assert info.beta == Decimal("1.05")
        assert info.maturity_date is None

    def test_bond_info_creation(self) -> None:
        info = InstrumentInfo(
            security_id="US912828YK09 Govt",
            name="US Treasury 2.875 05/15/28",
            asset_class=AssetClass.BOND,
            currency="USD",
            maturity_date=date(2028, 5, 15),
            coupon_rate=Decimal("0.02875"),
            modified_duration_years=Decimal("2.31"),
        )
        assert info.asset_class == AssetClass.BOND
        assert info.maturity_date == date(2028, 5, 15)
        assert info.modified_duration_years == Decimal("2.31")
        assert info.spread_duration_years is None

    def test_bond_info_with_spread_duration(self) -> None:
        """InstrumentInfo accepts spread_duration_years for corporate bonds."""
        info = InstrumentInfo(
            security_id="XS2543791470 Corp",
            name="LVMH 3.5 06/15/31",
            asset_class=AssetClass.BOND,
            currency="EUR",
            maturity_date=date(2031, 6, 15),
            coupon_rate=Decimal("0.035"),
            modified_duration_years=Decimal("4.71"),
            spread_duration_years=Decimal("4.71"),
        )
        assert info.spread_duration_years == Decimal("4.71")

    def test_bond_info_spread_duration_zero(self) -> None:
        """spread_duration_years = 0.0 is valid (Phase 1 government bond convention)."""
        info = InstrumentInfo(
            security_id="US912828YK09 Govt",
            name="US Treasury 2.875 05/15/28",
            asset_class=AssetClass.BOND,
            currency="USD",
            modified_duration_years=Decimal("2.31"),
            spread_duration_years=Decimal("0.0"),
        )
        assert info.spread_duration_years == Decimal("0.0")

    def test_equity_spread_duration_defaults_none(self) -> None:
        """Equity instruments have no spread_duration_years by default."""
        info = InstrumentInfo(
            security_id="AAPL US Equity",
            name="Apple Inc",
            asset_class=AssetClass.EQUITY,
            currency="USD",
        )
        assert info.spread_duration_years is None

    def test_fx_info_minimal(self) -> None:
        info = InstrumentInfo(
            security_id="EURUSD Curncy",
            name="Euro / US Dollar",
            asset_class=AssetClass.FX,
            currency="USD",
        )
        assert info.asset_class == AssetClass.FX
        assert info.beta is None
        assert info.maturity_date is None


class TestFXRate:
    """Tests for FXRate schema."""

    def test_fx_rate_creation(self) -> None:
        rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            date=date(2026, 6, 10),
            rate=Decimal("1.0850"),
        )
        assert rate.from_currency == "EUR"
        assert rate.to_currency == "USD"
        assert rate.rate == Decimal("1.0850")

    def test_fx_rate_accepts_string_decimal(self) -> None:
        rate = FXRate(
            from_currency="EUR",
            to_currency="USD",
            date=date(2026, 6, 10),
            rate="1.0850",
        )
        assert isinstance(rate.rate, Decimal)
        assert rate.rate == Decimal("1.0850")
