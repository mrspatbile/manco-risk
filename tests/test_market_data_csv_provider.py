"""Tests for CSVProvider market data implementation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from manco_risk.common import (
    FXRateNotAvailableError,
    InsufficientPriceDataError,
    SecurityNotFoundError,
)
from manco_risk.market_data import CSVProvider


@pytest.fixture
def provider() -> CSVProvider:
    """Create a CSVProvider instance with sample data."""
    data_dir = Path(__file__).parent.parent / "data"
    return CSVProvider(data_dir=data_dir)


class TestGetInstrumentInfo:
    """Tests for get_instrument_info method."""

    def test_get_equity_info(self, provider: CSVProvider) -> None:
        info = provider.get_instrument_info("SPY US Equity")
        assert info.security_id == "SPY US Equity"
        assert info.name == "SPDR S&P 500 ETF"
        assert info.currency == "USD"
        assert info.beta == Decimal("1.00")

    def test_get_bond_info(self, provider: CSVProvider) -> None:
        info = provider.get_instrument_info("US912828YK09 Govt")
        assert info.name == "US Treasury 2.875 05/15/28"
        assert info.maturity_date == date(2028, 5, 15)
        assert info.coupon_rate == Decimal("0.02875")
        assert info.modified_duration_years == Decimal("2.31")

    def test_government_bond_spread_duration_zero(self, provider: CSVProvider) -> None:
        """Government bonds carry spread_duration_years = 0.0 in Phase 1 sample data."""
        for sec_id in ("US912828YK09 Govt", "US912810TM79 Govt", "DBR 0 08/15/29 Govt"):
            info = provider.get_instrument_info(sec_id)
            assert info.spread_duration_years == Decimal("0.0"), (
                f"{sec_id}: expected spread_duration_years=0.0, got {info.spread_duration_years}"
            )

    def test_corporate_bond_spread_duration(self, provider: CSVProvider) -> None:
        """Corporate bond has positive spread_duration_years from CSV."""
        info = provider.get_instrument_info("XS2543791470 Corp")
        assert info.spread_duration_years == Decimal("4.71")

    def test_equity_spread_duration_none(self, provider: CSVProvider) -> None:
        """Equity instruments have no spread_duration_years."""
        info = provider.get_instrument_info("SPY US Equity")
        assert info.spread_duration_years is None

    def test_get_fx_info(self, provider: CSVProvider) -> None:
        info = provider.get_instrument_info("EURUSD Curncy")
        assert info.security_id == "EURUSD Curncy"
        assert info.asset_class.value == "FX"

    def test_security_not_found(self, provider: CSVProvider) -> None:
        with pytest.raises(SecurityNotFoundError):
            provider.get_instrument_info("UNKNOWN Equity")

    def test_all_instruments_loadable(self, provider: CSVProvider) -> None:
        """Verify all instruments in CSV are loadable."""
        instruments = [
            "SPY US Equity",
            "AAPL US Equity",
            "MSFT US Equity",
            "JPM US Equity",
            "GLD US Equity",
            "TLT US Equity",
            "US912828YK09 Govt",
            "US912810TM79 Govt",
            "DBR 0 08/15/29 Govt",
            "XS2543791470 Corp",
            "EURUSD Curncy",
            "GBPUSD Curncy",
            "SPX Index",
            "SX5E Index",
        ]
        for sec_id in instruments:
            info = provider.get_instrument_info(sec_id)
            assert info.security_id == sec_id


class TestGetPrice:
    """Tests for get_price method."""

    def test_get_price_exact_date(self, provider: CSVProvider) -> None:
        price = provider.get_price("SPY US Equity", date(2026, 6, 10))
        assert price.security_id == "SPY US Equity"
        assert price.date == date(2026, 6, 10)
        assert isinstance(price.price, Decimal)
        assert price.currency == "USD"

    def test_get_price_with_previous_business_day_fallback(self, provider: CSVProvider) -> None:
        # Request a Saturday (2026-06-13)
        # Should return the last available price before that date
        price = provider.get_price("SPY US Equity", date(2026, 6, 13))
        # Should get Friday's price (2026-06-12)
        assert price.date <= date(2026, 6, 13)
        assert price.date.weekday() <= 4  # Monday=0, Friday=4

    def test_get_price_security_not_found(self, provider: CSVProvider) -> None:
        with pytest.raises(SecurityNotFoundError):
            provider.get_price("UNKNOWN Equity", date(2026, 6, 10))

    def test_get_price_before_data_range(self, provider: CSVProvider) -> None:
        with pytest.raises(InsufficientPriceDataError):
            provider.get_price("SPY US Equity", date(2020, 1, 1))

    def test_get_price_multiple_securities(self, provider: CSVProvider) -> None:
        """Verify get_price works for different securities."""
        securities = ["SPY US Equity", "AAPL US Equity", "US912828YK09 Govt"]
        for sec_id in securities:
            price = provider.get_price(sec_id, date(2026, 6, 10))
            assert price.security_id == sec_id
            assert price.price > 0


class TestGetPriceHistory:
    """Tests for get_price_history method."""

    def test_get_price_history_valid_range(self, provider: CSVProvider) -> None:
        history = provider.get_price_history("SPY US Equity", date(2026, 1, 2), date(2026, 1, 31))
        assert history.security_id == "SPY US Equity"
        assert len(history.prices) > 0
        assert history.prices[0].date >= date(2026, 1, 2)
        assert history.prices[-1].date <= date(2026, 1, 31)

    def test_price_history_sorted_by_date(self, provider: CSVProvider) -> None:
        history = provider.get_price_history("SPY US Equity", date(2026, 1, 1), date(2026, 6, 10))
        dates = [p.date for p in history.prices]
        assert dates == sorted(dates)

    def test_price_history_no_gap_filling(self, provider: CSVProvider) -> None:
        """Verify that gaps (weekends) are not filled."""
        history = provider.get_price_history("SPY US Equity", date(2026, 1, 1), date(2026, 1, 31))
        # Check that we have business days only (no Saturdays/Sundays)
        for price in history.prices:
            assert price.date.weekday() < 5

    def test_price_history_security_not_found(self, provider: CSVProvider) -> None:
        with pytest.raises(SecurityNotFoundError):
            provider.get_price_history("UNKNOWN Equity", date(2026, 1, 1), date(2026, 6, 10))

    def test_price_history_no_data_in_range(self, provider: CSVProvider) -> None:
        with pytest.raises(InsufficientPriceDataError):
            provider.get_price_history("SPY US Equity", date(2020, 1, 1), date(2020, 1, 31))

    def test_price_history_single_date(self, provider: CSVProvider) -> None:
        history = provider.get_price_history("SPY US Equity", date(2026, 6, 10), date(2026, 6, 10))
        assert len(history.prices) >= 1
        assert history.prices[0].date == date(2026, 6, 10)

    def test_price_history_large_range(self, provider: CSVProvider) -> None:
        """Verify history works for multi-month range."""
        history = provider.get_price_history("SPY US Equity", date(2025, 12, 1), date(2026, 6, 10))
        assert len(history.prices) > 100


class TestGetFXRate:
    """Tests for get_fx_rate method."""

    def test_get_fx_rate_eur_usd(self, provider: CSVProvider) -> None:
        rate = provider.get_fx_rate("EUR", "USD", date(2026, 6, 10))
        assert rate.from_currency == "EUR"
        assert rate.to_currency == "USD"
        assert isinstance(rate.rate, Decimal)
        assert rate.rate > 0

    def test_get_fx_rate_gbp_usd(self, provider: CSVProvider) -> None:
        rate = provider.get_fx_rate("GBP", "USD", date(2026, 6, 10))
        assert rate.from_currency == "GBP"
        assert rate.to_currency == "USD"
        assert rate.date == date(2026, 6, 10)

    def test_get_fx_rate_with_fallback(self, provider: CSVProvider) -> None:
        # Request a Saturday (2026-06-13)
        # Should return the last available rate before that date
        rate = provider.get_fx_rate("EUR", "USD", date(2026, 6, 13))
        assert rate.date <= date(2026, 6, 13)
        assert rate.from_currency == "EUR"
        assert rate.to_currency == "USD"

    def test_get_fx_rate_currency_pair_not_found(self, provider: CSVProvider) -> None:
        with pytest.raises(FXRateNotAvailableError):
            provider.get_fx_rate("USD", "JPY", date(2026, 6, 10))

    def test_get_fx_rate_before_data_range(self, provider: CSVProvider) -> None:
        with pytest.raises(FXRateNotAvailableError):
            provider.get_fx_rate("EUR", "USD", date(2020, 1, 1))

    def test_get_fx_rate_both_pairs(self, provider: CSVProvider) -> None:
        """Verify both available FX pairs work."""
        for from_ccy, to_ccy in [("EUR", "USD"), ("GBP", "USD")]:
            rate = provider.get_fx_rate(from_ccy, to_ccy, date(2026, 6, 10))
            assert rate.from_currency == from_ccy
            assert rate.to_currency == to_ccy


class TestProviderInitialization:
    """Tests for CSVProvider initialization."""

    def test_provider_loads_all_data(self, provider: CSVProvider) -> None:
        """Verify provider successfully loads instruments, prices, and FX rates."""
        assert len(provider._instruments) > 0
        assert len(provider._prices) > 0
        assert len(provider._fx_rates) > 0

    def test_missing_instruments_csv_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            CSVProvider(data_dir="/nonexistent/path")

    def test_consistent_data_across_methods(self, provider: CSVProvider) -> None:
        """Verify currency consistency between different methods."""
        info = provider.get_instrument_info("SPY US Equity")
        price = provider.get_price("SPY US Equity", date(2026, 6, 10))
        assert info.currency == price.currency
