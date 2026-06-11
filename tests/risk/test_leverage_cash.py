"""Tests for cash and cash-equivalent leverage exposure engine.

Validates exposure treatment for cash positions:
- Base-currency cash is excluded from leverage (zero gross/commitment exposure)
- Foreign-currency cash is tracked as unsupported
- Raw exposure is tracked for reference
"""

from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
)
from manco_risk.risk.leverage.cash_engine import CashExposureEngine


@pytest.fixture
def sample_base_currency_cash():
    """Sample base-currency cash position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=1,
        isin="N/A",
        valuation_date="2026-06-10",
        quantity=Decimal("100000"),
        market_value=Decimal("100000"),
        position_currency="EUR",
        asset_class="Cash",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("100000"),
        fund_base_currency="EUR",
        weight=Decimal("0.25"),
    )


@pytest.fixture
def sample_usd_cash():
    """Sample USD cash position (foreign currency relative to EUR fund)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="N/A",
        valuation_date="2026-06-10",
        quantity=Decimal("50000"),
        market_value=Decimal("50000"),
        position_currency="USD",
        asset_class="Cash",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("46000"),
        fund_base_currency="EUR",
        weight=Decimal("0.115"),
    )


@pytest.fixture
def sample_equity_position():
    """Sample equity position (non-cash)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=3,
        isin="US0378331005",
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("30000"),
        position_currency="USD",
        asset_class="Equity",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("27600"),
        fund_base_currency="EUR",
        weight=Decimal("0.069"),
    )


@pytest.fixture
def engine():
    """Cash exposure engine."""
    return CashExposureEngine()


class TestCashExposureEngine:
    """Test cash and cash-equivalent exposure calculation."""

    def test_single_base_currency_cash_position(self, engine, sample_base_currency_cash):
        """Single base-currency cash position is classified as cash source."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        pos = result.position_contributions[0]
        assert pos.position_id == 1
        assert pos.asset_class == "Cash"
        assert pos.source == LeverageSource.CASH_AND_CASH_EQUIVALENT
        assert pos.treatment == ExposureTreatment.EXCLUDED

    def test_raw_exposure_equals_absolute_market_value(self, engine, sample_base_currency_cash):
        """Raw exposure equals absolute market value."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.raw_exposure == Decimal("100000")
        assert pos.raw_exposure == abs(pos.market_value_base_ccy)

    def test_gross_exposure_is_zero(self, engine, sample_base_currency_cash):
        """Gross exposure is zero (excluded from leverage)."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.gross_exposure == Decimal("0")

    def test_commitment_exposure_is_zero(self, engine, sample_base_currency_cash):
        """Commitment exposure is zero (Phase 1)."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.commitment_exposure == Decimal("0")

    def test_treatment_is_excluded(self, engine, sample_base_currency_cash):
        """Treatment is EXCLUDED."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.treatment == ExposureTreatment.EXCLUDED

    def test_exclusion_reason_populated(self, engine, sample_base_currency_cash):
        """Exclusion reason is populated."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.exclusion_reason is not None
        assert "excluded" in pos.exclusion_reason.lower()
        assert "cash" in pos.exclusion_reason.lower()

    def test_non_cash_positions_ignored(self, engine, sample_equity_position):
        """Non-cash positions are ignored."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert result.source_contribution is None

    def test_mixed_portfolio_only_cash(
        self, engine, sample_base_currency_cash, sample_equity_position
    ):
        """Mixed portfolio includes only cash positions."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash, sample_equity_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        assert result.position_contributions[0].asset_class == "Cash"

    def test_no_cash_positions_returns_none_source(self, engine, sample_equity_position):
        """No cash positions returns None source contribution."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert result.source_contribution is None

    def test_empty_portfolio_returns_none_source(self, engine):
        """Empty portfolio returns None source contribution."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("100000"),
            positions=[],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert result.source_contribution is None

    def test_negative_cash_uses_absolute_raw_exposure(self, engine):
        """Negative cash market value uses absolute raw exposure."""
        cash_position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="N/A",
            valuation_date="2026-06-10",
            quantity=Decimal("0"),
            market_value=Decimal("0"),
            position_currency="EUR",
            asset_class="Cash",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("50000"),
            fund_base_currency="EUR",
            weight=Decimal("0.125"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[cash_position],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.raw_exposure == Decimal("50000")

    def test_foreign_currency_cash_not_silently_treated(self, engine, sample_usd_cash):
        """Foreign-currency cash is not silently treated as base-currency cash."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_usd_cash],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert len(result.unsupported_exposures) == 1
        assert len(result.warnings) == 1
        unsupported = result.unsupported_exposures[0]
        assert "USD" in unsupported.reason or "Foreign" in unsupported.reason

    def test_source_contribution_zero_exposure(self, engine, sample_base_currency_cash):
        """Source contribution has zero gross and commitment exposure."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("0")
        assert result.source_contribution.commitment_exposure == Decimal("0")

    def test_source_contribution_excluded_treatment(self, engine, sample_base_currency_cash):
        """Source contribution treatment is EXCLUDED."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        assert result.source_contribution is not None
        assert result.source_contribution.treatment == ExposureTreatment.EXCLUDED
        assert result.source_contribution.exclusion_reason is not None

    def test_no_unsupported_for_valid_base_currency_cash(self, engine, sample_base_currency_cash):
        """No unsupported exposure for valid base-currency cash."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        assert len(result.unsupported_exposures) == 0

    def test_multiple_base_currency_cash_aggregates(self, engine):
        """Multiple base-currency cash positions aggregate correctly."""
        cash1 = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="N/A",
            valuation_date="2026-06-10",
            quantity=Decimal("50000"),
            market_value=Decimal("50000"),
            position_currency="EUR",
            asset_class="Cash",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("50000"),
            fund_base_currency="EUR",
            weight=Decimal("0.125"),
        )
        cash2 = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=2,
            isin="N/A",
            valuation_date="2026-06-10",
            quantity=Decimal("75000"),
            market_value=Decimal("75000"),
            position_currency="EUR",
            asset_class="Cash",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("75000"),
            fund_base_currency="EUR",
            weight=Decimal("0.1875"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[cash1, cash2],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 2
        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("0")
        assert result.source_contribution.commitment_exposure == Decimal("0")

    def test_mixed_base_and_foreign_currency_cash(
        self, engine, sample_base_currency_cash, sample_usd_cash
    ):
        """Mixed base and foreign-currency cash correctly classified."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash, sample_usd_cash],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        assert result.position_contributions[0].position_id == 1
        assert len(result.unsupported_exposures) == 1
        assert result.unsupported_exposures[0].position_id == 2
        assert len(result.warnings) == 1

    def test_result_model_is_frozen(self, engine, sample_base_currency_cash):
        """Result model is immutable."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        with pytest.raises(Exception):  # Pydantic raises on frozen model
            result.position_contributions = []

    def test_source_contribution_uses_cash_source(self, engine, sample_base_currency_cash):
        """Source contribution uses CASH_AND_CASH_EQUIVALENT source."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[sample_base_currency_cash],
        )

        result = engine.calculate(portfolio)

        assert result.source_contribution is not None
        assert result.source_contribution.source == LeverageSource.CASH_AND_CASH_EQUIVALENT

    def test_gbp_cash_in_eur_fund_marked_unsupported(self, engine):
        """GBP cash in EUR fund is marked as unsupported."""
        gbp_cash = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=1,
            position_id=1,
            isin="N/A",
            valuation_date="2026-06-10",
            quantity=Decimal("20000"),
            market_value=Decimal("20000"),
            position_currency="GBP",
            asset_class="Cash",
            instrument_currency="GBP",
            market_value_base_ccy=Decimal("23400"),
            fund_base_currency="EUR",
            weight=Decimal("0.0585"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("400000"),
            positions=[gbp_cash],
        )

        result = engine.calculate(portfolio)

        assert len(result.unsupported_exposures) == 1
        unsupported = result.unsupported_exposures[0]
        assert "GBP" in unsupported.reason
        assert len(result.warnings) > 0
