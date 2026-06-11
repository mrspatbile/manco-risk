"""Tests for physical instrument leverage exposure engine.

Validates exposure calculation for physical instruments (equities, bonds, ETFs, indices).
"""

from decimal import Decimal

import pytest

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
    PhysicalInstrumentExposureEngine,
)


@pytest.fixture
def sample_equity_position():
    """Sample equity position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=1,
        isin="US0378331005",
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=Decimal("30000"),
        position_currency="USD",
        asset_class="Equity",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("30000"),
        fund_base_currency="EUR",
        weight=Decimal("0.1"),
    )


@pytest.fixture
def sample_bond_position():
    """Sample bond position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="DE0000000001",
        valuation_date="2026-06-10",
        quantity=Decimal("1000"),
        market_value=Decimal("102000"),
        position_currency="EUR",
        asset_class="Bond",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("102000"),
        fund_base_currency="EUR",
        weight=Decimal("0.3"),
        modified_duration=Decimal("5.5"),
    )


@pytest.fixture
def sample_index_position():
    """Sample index position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=3,
        isin="IE00B4L5Y983",
        valuation_date="2026-06-10",
        quantity=Decimal("50"),
        market_value=Decimal("15000"),
        position_currency="EUR",
        asset_class="Index",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("15000"),
        fund_base_currency="EUR",
        weight=Decimal("0.05"),
    )


@pytest.fixture
def sample_fx_position():
    """Sample FX position (not physical instrument)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=4,
        isin="N/A",
        valuation_date="2026-06-10",
        quantity=Decimal("100000"),
        market_value=Decimal("100000"),
        position_currency="USD",
        asset_class="FX",
        instrument_currency="USD",
        market_value_base_ccy=Decimal("92000"),
        fund_base_currency="EUR",
        weight=Decimal("0.27"),
    )


@pytest.fixture
def sample_cash_position():
    """Sample cash position (not physical instrument)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=5,
        isin="N/A",
        valuation_date="2026-06-10",
        quantity=Decimal("50000"),
        market_value=Decimal("50000"),
        position_currency="EUR",
        asset_class="Cash",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("50000"),
        fund_base_currency="EUR",
        weight=Decimal("0.15"),
    )


@pytest.fixture
def sample_etf_position():
    """Sample ETF position (physical instrument)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=6,
        isin="IE00B4L5Y983",
        valuation_date="2026-06-10",
        quantity=Decimal("200"),
        market_value=Decimal("25000"),
        position_currency="EUR",
        asset_class="ETF",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("25000"),
        fund_base_currency="EUR",
        weight=Decimal("0.075"),
    )


@pytest.fixture
def engine():
    """Physical instrument exposure engine."""
    return PhysicalInstrumentExposureEngine()


class TestPhysicalInstrumentExposureEngine:
    """Test physical instrument exposure calculation."""

    def test_single_equity_position(self, engine, sample_equity_position):
        """Single equity position exposure equals absolute market value."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        pos = result.position_contributions[0]
        assert pos.position_id == 1
        assert pos.asset_class == "Equity"
        assert pos.source == LeverageSource.PHYSICAL_INSTRUMENT
        assert pos.treatment == ExposureTreatment.INCLUDED
        assert pos.raw_exposure == Decimal("30000")
        assert pos.gross_exposure == Decimal("30000")
        assert pos.commitment_exposure == Decimal("30000")
        assert pos.exclusion_reason is None

    def test_bond_position_no_duration_warning(self, engine, sample_bond_position):
        """Bond exposure uses market value; no duration warning emitted."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_bond_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        assert len(result.warnings) == 0
        pos = result.position_contributions[0]
        assert pos.asset_class == "Bond"
        assert pos.gross_exposure == Decimal("102000")
        assert pos.commitment_exposure == Decimal("102000")

    def test_etf_position_included(self, engine, sample_etf_position):
        """ETF position is included as physical instrument."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_etf_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        pos = result.position_contributions[0]
        assert pos.asset_class == "ETF"
        assert pos.source == LeverageSource.PHYSICAL_INSTRUMENT
        assert pos.gross_exposure == Decimal("25000")

    def test_index_position_included(self, engine, sample_index_position):
        """Index position is included as physical instrument."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_index_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 1
        pos = result.position_contributions[0]
        assert pos.asset_class == "Index"
        assert pos.gross_exposure == Decimal("15000")

    def test_cash_position_ignored(self, engine, sample_cash_position):
        """Cash position is ignored by physical instrument engine."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_cash_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert result.source_contribution is None
        assert len(result.warnings) == 0

    def test_fx_position_ignored(self, engine, sample_fx_position):
        """FX position is ignored by physical instrument engine."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_fx_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 0
        assert result.source_contribution is None

    def test_mixed_portfolio_aggregates_physical_only(
        self, engine, sample_equity_position, sample_bond_position, sample_cash_position
    ):
        """Mixed portfolio aggregates only physical instruments."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position, sample_bond_position, sample_cash_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 2
        assert result.position_contributions[0].asset_class == "Equity"
        assert result.position_contributions[1].asset_class == "Bond"
        assert result.source_contribution is not None

    def test_no_physical_instruments_returns_none_source(self, engine):
        """Portfolio with no physical instruments returns None source contribution."""
        cash_only = EnrichedPosition(
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
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("100000"),
            positions=[cash_only],
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

    def test_source_contribution_aggregates_positions(
        self, engine, sample_equity_position, sample_bond_position, sample_index_position
    ):
        """Source contribution aggregates all position exposures."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position, sample_bond_position, sample_index_position],
        )

        result = engine.calculate(portfolio)

        expected_total = Decimal("30000") + Decimal("102000") + Decimal("15000")
        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == expected_total
        assert result.source_contribution.commitment_exposure == expected_total
        assert result.source_contribution.source == LeverageSource.PHYSICAL_INSTRUMENT
        assert result.source_contribution.treatment == ExposureTreatment.INCLUDED

    def test_source_contribution_equals_sum_of_positions(
        self, engine, sample_equity_position, sample_bond_position
    ):
        """Source contribution gross exposure equals sum of position exposures."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position, sample_bond_position],
        )

        result = engine.calculate(portfolio)

        sum_of_positions = sum(p.gross_exposure for p in result.position_contributions)
        assert result.source_contribution.gross_exposure == sum_of_positions

    def test_commitment_exposure_equals_gross_for_physical(self, engine, sample_equity_position):
        """Commitment exposure equals gross exposure for Phase 1 physical instruments."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.commitment_exposure == pos.gross_exposure
        assert result.source_contribution.commitment_exposure == (
            result.source_contribution.gross_exposure
        )

    def test_position_contribution_fields_populated(self, engine, sample_equity_position):
        """Position contribution has all required fields populated."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        pos = result.position_contributions[0]
        assert pos.position_id == sample_equity_position.position_id
        assert pos.isin == sample_equity_position.isin
        assert pos.asset_class == sample_equity_position.asset_class
        assert pos.market_value_base_ccy == sample_equity_position.market_value_base_ccy
        assert pos.source == LeverageSource.PHYSICAL_INSTRUMENT
        assert pos.treatment == ExposureTreatment.INCLUDED

    def test_no_warnings_on_valid_portfolio(self, engine, sample_equity_position):
        """Valid physical instrument portfolio produces no warnings."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.warnings) == 0

    def test_no_unsupported_exposures_for_known_asset_classes(
        self, engine, sample_equity_position, sample_bond_position
    ):
        """Known asset classes do not produce unsupported exposure records."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position, sample_bond_position],
        )

        result = engine.calculate(portfolio)

        assert len(result.unsupported_exposures) == 0

    def test_large_portfolio_aggregates_correctly(self, engine):
        """Large portfolio with many positions aggregates correctly."""
        positions = [
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=1,
                position_id=i,
                isin=f"ISIN{i:06d}",
                valuation_date="2026-06-10",
                quantity=Decimal("100"),
                market_value=Decimal("10000"),
                position_currency="EUR",
                asset_class="Equity",
                instrument_currency="EUR",
                market_value_base_ccy=Decimal("10000"),
                fund_base_currency="EUR",
                weight=Decimal("0.01"),
            )
            for i in range(1, 51)
        ]

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("500000"),
            positions=positions,
        )

        result = engine.calculate(portfolio)

        assert len(result.position_contributions) == 50
        expected_total = Decimal("10000") * 50
        assert result.source_contribution.gross_exposure == expected_total

    def test_result_model_is_frozen(self, engine, sample_equity_position):
        """Result model is immutable."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("300000"),
            positions=[sample_equity_position],
        )

        result = engine.calculate(portfolio)

        with pytest.raises(Exception):  # Pydantic raises on frozen model
            result.position_contributions = []
