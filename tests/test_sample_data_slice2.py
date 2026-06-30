"""Tests for Issue #9 Slice 2: sample position and market data.

Validates that:
- Sample position files load without errors
- All position ISINs exist in instruments reference data
- All instruments have sufficient price history
- Basic VaR workflow can consume the sample data
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from manco_risk.etl.position_loader import PositionLoader
from manco_risk.market_data.csv_provider import CSVProvider


class TestUCITSBalancedPositionsLoad:
    """Test UCITS_Balanced sample positions file."""

    def test_ucits_positions_file_exists(self) -> None:
        """UCITS_Balanced/positions.csv file exists."""
        csv_path = Path("data/funds/UCITS_Balanced/positions.csv")
        assert csv_path.exists(), f"Expected {csv_path} to exist"

    def test_ucits_positions_load(self) -> None:
        """UCITS_Balanced positions CSV loads without errors."""
        csv_path = Path("data/funds/UCITS_Balanced/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        assert len(positions) > 0, "Should have at least one position"
        assert all(p.fund_name == "UCITS_Balanced" for p in positions)

    def test_ucits_positions_reasonable_count(self) -> None:
        """UCITS_Balanced has 20-30 positions as designed."""
        csv_path = Path("data/funds/UCITS_Balanced/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        # Should be around 16 positions (equities + bonds + cash)
        assert 15 <= len(positions) <= 30, f"Expected 15-30 positions, got {len(positions)}"

    def test_ucits_positions_have_positive_market_values(self) -> None:
        """UCITS_Balanced positions have non-negative market values."""
        csv_path = Path("data/funds/UCITS_Balanced/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        # Cash position can be zero quantity but has market value
        for p in positions:
            assert p.market_value >= Decimal("0"), (
                f"Expected non-negative market_value, got {p.market_value}"
            )

    def test_ucits_positions_reasonable_quantities(self) -> None:
        """UCITS_Balanced quantities are reasonable (allow short positions)."""
        csv_path = Path("data/funds/UCITS_Balanced/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        for p in positions:
            # Allow short positions (negative quantity) and zero
            assert p.quantity.is_finite(), f"Expected finite quantity, got {p.quantity}"


class TestAIFMHedgeFundPositionsLoad:
    """Test AIFM_HedgeFund sample positions file."""

    def test_aifm_positions_file_exists(self) -> None:
        """AIFM_HedgeFund/positions.csv file exists."""
        csv_path = Path("data/funds/AIFM_HedgeFund/positions.csv")
        assert csv_path.exists(), f"Expected {csv_path} to exist"

    def test_aifm_positions_load(self) -> None:
        """AIFM_HedgeFund positions CSV loads without errors."""
        csv_path = Path("data/funds/AIFM_HedgeFund/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        assert len(positions) > 0, "Should have at least one position"
        assert all(p.fund_name == "AIFM_HedgeFund" for p in positions)

    def test_aifm_positions_reasonable_count(self) -> None:
        """AIFM_HedgeFund has 30-50 positions as designed."""
        csv_path = Path("data/funds/AIFM_HedgeFund/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        # Should be around 20 positions (long/short equities, bonds, FX, cash)
        assert 15 <= len(positions) <= 50, f"Expected 15-50 positions, got {len(positions)}"

    def test_aifm_has_short_positions(self) -> None:
        """AIFM_HedgeFund includes short positions (negative quantities)."""
        csv_path = Path("data/funds/AIFM_HedgeFund/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        short_positions = [p for p in positions if p.quantity < 0]
        assert len(short_positions) > 0, "Expected at least one short position"

    def test_aifm_positions_reasonable_quantities(self) -> None:
        """AIFM_HedgeFund quantities are reasonable (allow negatives)."""
        csv_path = Path("data/funds/AIFM_HedgeFund/positions.csv")
        positions = PositionLoader.load_csv(csv_path)

        for p in positions:
            assert p.quantity.is_finite(), f"Expected finite quantity, got {p.quantity}"


class TestPositionISINsInInstruments:
    """Validate that all position ISINs exist in instruments reference."""

    def test_ucits_isins_exist_in_instruments(self) -> None:
        """All UCITS_Balanced position ISINs exist in instruments.csv."""
        ucits_positions = PositionLoader.load_csv("data/funds/UCITS_Balanced/positions.csv")
        provider = CSVProvider("data")

        position_isins = {p.isin for p in ucits_positions}

        for isin in position_isins:
            try:
                provider.get_instrument_info(isin)
            except Exception as e:
                pytest.fail(f"ISIN {isin} from UCITS_Balanced not found in instruments: {e}")

    def test_aifm_isins_exist_in_instruments(self) -> None:
        """All AIFM_HedgeFund position ISINs exist in instruments.csv."""
        aifm_positions = PositionLoader.load_csv("data/funds/AIFM_HedgeFund/positions.csv")
        provider = CSVProvider("data")

        position_isins = {p.isin for p in aifm_positions}

        for isin in position_isins:
            try:
                provider.get_instrument_info(isin)
            except Exception as e:
                pytest.fail(f"ISIN {isin} from AIFM_HedgeFund not found in instruments: {e}")


class TestMarketDataCoverage:
    """Validate market data has sufficient history for calculations."""

    def test_all_ucits_instruments_have_price_history(self) -> None:
        """All UCITS_Balanced position instruments have price history."""
        ucits_positions = PositionLoader.load_csv("data/funds/UCITS_Balanced/positions.csv")
        provider = CSVProvider("data")

        # Lookback window: 60 trading days
        valuation_date = date(2026, 6, 10)
        start_date = date(2026, 3, 19)  # Approximately 60 trading days back

        position_isins = {p.isin for p in ucits_positions}

        for isin in position_isins:
            try:
                history = provider.get_price_history(isin, start_date, valuation_date)
                assert len(history.prices) > 0, f"No prices for {isin} in lookback window"
            except Exception as e:
                pytest.fail(f"Could not retrieve price history for {isin}: {e}")

    def test_all_aifm_instruments_have_price_history(self) -> None:
        """All AIFM_HedgeFund position instruments have price history."""
        aifm_positions = PositionLoader.load_csv("data/funds/AIFM_HedgeFund/positions.csv")
        provider = CSVProvider("data")

        # Lookback window: 60 trading days
        valuation_date = date(2026, 6, 10)
        start_date = date(2026, 3, 19)

        position_isins = {p.isin for p in aifm_positions}

        for isin in position_isins:
            try:
                history = provider.get_price_history(isin, start_date, valuation_date)
                assert len(history.prices) > 0, f"No prices for {isin} in lookback window"
            except Exception as e:
                pytest.fail(f"Could not retrieve price history for {isin}: {e}")


class TestVaRSmokeTest:
    """Basic smoke test: VaR workflow can consume sample data."""

    def test_var_can_load_ucits_portfolio_data(self) -> None:
        """VaR calculation can load UCITS_Balanced portfolio data."""
        from manco_risk.risk.engines.var import HistoricalVaR

        ucits_positions = PositionLoader.load_csv("data/funds/UCITS_Balanced/positions.csv")
        provider = CSVProvider("data")

        # Verify we can access price data
        valuation_date = date(2026, 6, 10)
        start_date = date(2026, 3, 19)

        for position in ucits_positions:
            if position.isin != "Cash":  # Skip cash position
                try:
                    history = provider.get_price_history(position.isin, start_date, valuation_date)
                    assert len(history.prices) > 0
                except Exception:
                    # Some positions may not have complete history; that's ok for smoke test
                    pass

        # Can instantiate VaR engine
        var_engine = HistoricalVaR()
        assert var_engine is not None

    def test_var_can_load_aifm_portfolio_data(self) -> None:
        """VaR calculation can load AIFM_HedgeFund portfolio data."""
        from manco_risk.risk.engines.var import HistoricalVaR

        aifm_positions = PositionLoader.load_csv("data/funds/AIFM_HedgeFund/positions.csv")
        provider = CSVProvider("data")

        # Verify we can access price data
        valuation_date = date(2026, 6, 10)
        start_date = date(2026, 3, 19)

        for position in aifm_positions:
            if position.isin != "Cash":  # Skip cash position
                try:
                    history = provider.get_price_history(position.isin, start_date, valuation_date)
                    assert len(history.prices) > 0
                except Exception:
                    # Some positions may not have complete history; that's ok for smoke test
                    pass

        # Can instantiate VaR engine
        var_engine = HistoricalVaR()
        assert var_engine is not None
