"""Tests for position enrichment engine."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.common import AssetClass
from manco_risk.etl import (
    InstrumentReferenceNotFoundError,
    MissingFXRateError,
    PositionEnricher,
    PositionEnrichmentError,
)
from manco_risk.market_data.schemas import InstrumentInfo


class MockInstrument:
    """Mock Instrument for testing."""

    def __init__(
        self,
        isin: str,
        asset_class: str,
        currency: str,
        modified_duration: Decimal | None = None,
    ) -> None:
        self.isin = isin
        self.asset_class = asset_class
        self.currency = currency
        self.modified_duration = modified_duration


class MockPosition:
    """Mock Position for testing."""

    def __init__(
        self,
        position_id: int,
        position_snapshot_id: int,
        fund_id: int,
        isin: str,
        quantity: Decimal,
        market_value: Decimal,
        valuation_date: date = date(2026, 6, 10),
    ) -> None:
        self.position_id = position_id
        self.position_snapshot_id = position_snapshot_id
        self.fund_id = fund_id
        self.isin = isin
        self.quantity = quantity
        self.market_value = market_value
        self.valuation_date = valuation_date


class TestPositionEnricher:
    """Test PositionEnricher enrichment logic."""

    @staticmethod
    def make_enricher() -> PositionEnricher:
        """Create a PositionEnricher instance."""
        return PositionEnricher()

    def test_single_position_same_currency(self) -> None:
        """Enrich single position in fund base currency (no FX needed)."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        nav = Decimal("1000000.00")

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=nav,
            positions=[position],
            instruments_by_isin={"IE00B4L5Y983": instrument},
            fx_rates={},
        )

        assert portfolio.fund_id == 1
        assert portfolio.fund_base_currency == "EUR"
        assert len(portfolio.positions) == 1

        enriched = portfolio.positions[0]
        assert enriched.position_id == 1
        assert enriched.isin == "IE00B4L5Y983"
        assert enriched.position_currency == "EUR"
        assert enriched.market_value == Decimal("50000.00")
        assert enriched.market_value_base_ccy == Decimal("50000.00")
        assert enriched.weight == Decimal("50000.00") / nav

    def test_mixed_currency_portfolio_with_fx(self) -> None:
        """Enrich mixed-currency portfolio with FX rates provided."""
        enricher = self.make_enricher()

        positions = [
            MockPosition(
                position_id=1,
                position_snapshot_id=100,
                fund_id=1,
                isin="IE00B4L5Y983",
                quantity=Decimal("1000"),
                market_value=Decimal("50000.00"),  # EUR
            ),
            MockPosition(
                position_id=2,
                position_snapshot_id=100,
                fund_id=1,
                isin="US0378331005",
                quantity=Decimal("2000"),
                market_value=Decimal("220000.00"),  # USD
            ),
        ]

        instruments = {
            "IE00B4L5Y983": MockInstrument(
                isin="IE00B4L5Y983",
                asset_class="EQUITY",
                currency="EUR",
            ),
            "US0378331005": MockInstrument(
                isin="US0378331005",
                asset_class="EQUITY",
                currency="USD",
            ),
        }

        nav = Decimal("1000000.00")
        fx_rate_usd_eur = Decimal("0.92")

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=nav,
            positions=positions,
            instruments_by_isin=instruments,
            fx_rates={
                ("USD", "EUR"): fx_rate_usd_eur,
            },
        )

        assert len(portfolio.positions) == 2

        # First position (EUR): no conversion
        eur_enriched = portfolio.positions[0]
        assert eur_enriched.market_value_base_ccy == Decimal("50000.00")

        # Second position (USD): converted
        usd_enriched = portfolio.positions[1]
        expected_base_ccy = Decimal("220000.00") * fx_rate_usd_eur
        assert usd_enriched.market_value_base_ccy == expected_base_ccy

        # Total weight
        total_weight = (Decimal("50000.00") + expected_base_ccy) / nav
        assert portfolio.total_weight == total_weight

    def test_missing_fx_rate_raises_error(self) -> None:
        """Missing FX rate raises MissingFXRateError."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="US0378331005",
            quantity=Decimal("2000"),
            market_value=Decimal("220000.00"),  # USD
        )

        instrument = MockInstrument(
            isin="US0378331005",
            asset_class="EQUITY",
            currency="USD",
        )

        with pytest.raises(MissingFXRateError) as exc_info:
            enricher.enrich_portfolio(
                fund_id=1,
                fund_base_currency="EUR",
                valuation_date=date(2026, 6, 10),
                nav=Decimal("1000000.00"),
                positions=[position],
                instruments_by_isin={"US0378331005": instrument},
                fx_rates={},  # No FX rates provided
            )

        error = exc_info.value
        assert error.from_currency == "USD"
        assert error.to_currency == "EUR"
        assert error.position_id == 1

    def test_missing_instrument_raises_error(self) -> None:
        """Missing instrument reference raises InstrumentReferenceNotFoundError."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
        )

        with pytest.raises(InstrumentReferenceNotFoundError) as exc_info:
            enricher.enrich_portfolio(
                fund_id=1,
                fund_base_currency="EUR",
                valuation_date=date(2026, 6, 10),
                nav=Decimal("1000000.00"),
                positions=[position],
                instruments_by_isin={},  # Empty map
                fx_rates={},
            )

        error = exc_info.value
        assert error.isin == "IE00B4L5Y983"
        assert error.position_id == 1

    def test_short_position_with_negative_quantity(self) -> None:
        """Allow short positions with negative quantity."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("-500"),  # Short
            market_value=Decimal("25000.00"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"IE00B4L5Y983": instrument},
            fx_rates={},
        )

        enriched = portfolio.positions[0]
        assert enriched.quantity == Decimal("-500")
        assert enriched.weight == Decimal("25000.00") / Decimal("1000000.00")

    def test_zero_market_value_creates_zero_weight(self) -> None:
        """Position with zero market value has zero weight."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("0"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"IE00B4L5Y983": instrument},
            fx_rates={},
        )

        enriched = portfolio.positions[0]
        assert enriched.market_value_base_ccy == Decimal("0")
        assert enriched.weight == Decimal("0")

    def test_empty_portfolio(self) -> None:
        """Empty position list returns empty RiskReadyPortfolio."""
        enricher = self.make_enricher()

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[],
            instruments_by_isin={},
            fx_rates={},
        )

        assert len(portfolio.positions) == 0
        assert portfolio.total_weight == Decimal("0")
        assert portfolio.nav == Decimal("1000000.00")

    def test_decimal_precision_preserved(self) -> None:
        """Decimal precision is preserved through enrichment."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("123.456789"),
            market_value=Decimal("12345.6789123"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        nav = Decimal("1000000")

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=nav,
            positions=[position],
            instruments_by_isin={"IE00B4L5Y983": instrument},
            fx_rates={},
        )

        enriched = portfolio.positions[0]
        assert enriched.quantity == Decimal("123.456789")
        assert enriched.market_value == Decimal("12345.6789123")

        # Weight calculation should preserve precision
        expected_weight = Decimal("12345.6789123") / nav
        assert enriched.weight == expected_weight

    def test_nav_zero_rejected(self) -> None:
        """NAV of zero is rejected."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        with pytest.raises(PositionEnrichmentError) as exc_info:
            enricher.enrich_portfolio(
                fund_id=1,
                fund_base_currency="EUR",
                valuation_date=date(2026, 6, 10),
                nav=Decimal("0"),  # Invalid
                positions=[position],
                instruments_by_isin={"IE00B4L5Y983": instrument},
                fx_rates={},
            )

        assert "strictly positive" in str(exc_info.value).lower()

    def test_nav_negative_rejected(self) -> None:
        """Negative NAV is rejected."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        with pytest.raises(PositionEnrichmentError) as exc_info:
            enricher.enrich_portfolio(
                fund_id=1,
                fund_base_currency="EUR",
                valuation_date=date(2026, 6, 10),
                nav=Decimal("-100000.00"),  # Invalid
                positions=[position],
                instruments_by_isin={"IE00B4L5Y983": instrument},
                fx_rates={},
            )

        assert "strictly positive" in str(exc_info.value).lower()

    def test_durations_none_without_instrument_infos(self) -> None:
        """Both duration fields are None when instrument_infos_by_isin is not provided."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="DE0001102309",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
        )

        instrument = MockInstrument(
            isin="DE0001102309",
            asset_class="BOND",
            currency="EUR",
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"DE0001102309": instrument},
            fx_rates={},
        )

        enriched = portfolio.positions[0]
        assert enriched.modified_duration is None
        assert enriched.spread_duration is None

    def test_modified_duration_wired_from_instrument_info(self) -> None:
        """modified_duration is populated from InstrumentInfo.modified_duration_years."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="US912828YK09",
            quantity=Decimal("500"),
            market_value=Decimal("96300.00"),
        )

        instrument = MockInstrument(
            isin="US912828YK09",
            asset_class="BOND",
            currency="USD",
        )

        instrument_info = InstrumentInfo(
            security_id="US912828YK09 Govt",
            name="US Treasury 2.875 05/15/28",
            asset_class=AssetClass.BOND,
            currency="USD",
            modified_duration_years=Decimal("2.31"),
            spread_duration_years=Decimal("0.0"),
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="USD",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"US912828YK09": instrument},
            fx_rates={},
            instrument_infos_by_isin={"US912828YK09": instrument_info},
        )

        enriched = portfolio.positions[0]
        assert enriched.modified_duration == Decimal("2.31")

    def test_spread_duration_wired_from_instrument_info(self) -> None:
        """spread_duration is populated from InstrumentInfo.spread_duration_years."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="XS2543791470",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
        )

        instrument = MockInstrument(
            isin="XS2543791470",
            asset_class="BOND",
            currency="EUR",
        )

        instrument_info = InstrumentInfo(
            security_id="XS2543791470 Corp",
            name="LVMH 3.5 06/15/31",
            asset_class=AssetClass.BOND,
            currency="EUR",
            modified_duration_years=Decimal("4.71"),
            spread_duration_years=Decimal("4.71"),
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"XS2543791470": instrument},
            fx_rates={},
            instrument_infos_by_isin={"XS2543791470": instrument_info},
        )

        enriched = portfolio.positions[0]
        assert enriched.spread_duration == Decimal("4.71")

    def test_durations_none_when_isin_not_in_instrument_infos(self) -> None:
        """Durations remain None when the ISIN is absent from instrument_infos_by_isin."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="DE0001102309",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
        )

        instrument = MockInstrument(
            isin="DE0001102309",
            asset_class="BOND",
            currency="EUR",
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"DE0001102309": instrument},
            fx_rates={},
            instrument_infos_by_isin={},  # empty: ISIN not present
        )

        enriched = portfolio.positions[0]
        assert enriched.modified_duration is None
        assert enriched.spread_duration is None

    def test_equity_enrichment_unaffected_by_instrument_infos(self) -> None:
        """Existing equity enrichment works correctly when instrument_infos_by_isin provided."""
        enricher = self.make_enricher()

        position = MockPosition(
            position_id=1,
            position_snapshot_id=100,
            fund_id=1,
            isin="IE00B4L5Y983",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
        )

        instrument = MockInstrument(
            isin="IE00B4L5Y983",
            asset_class="EQUITY",
            currency="EUR",
        )

        equity_info = InstrumentInfo(
            security_id="IE00B4L5Y983",
            name="iShares Core MSCI World",
            asset_class=AssetClass.EQUITY,
            currency="EUR",
        )

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=Decimal("1000000.00"),
            positions=[position],
            instruments_by_isin={"IE00B4L5Y983": instrument},
            fx_rates={},
            instrument_infos_by_isin={"IE00B4L5Y983": equity_info},
        )

        enriched = portfolio.positions[0]
        assert enriched.market_value_base_ccy == Decimal("50000.00")
        assert enriched.modified_duration is None
        assert enriched.spread_duration is None

    def test_leveraged_portfolio_weight_gt_one(self) -> None:
        """Leveraged portfolio can have total weight > 1.0."""
        enricher = self.make_enricher()

        positions = [
            MockPosition(
                position_id=1,
                position_snapshot_id=100,
                fund_id=1,
                isin="IE00B4L5Y983",
                quantity=Decimal("6000"),
                market_value=Decimal("600000.00"),
            ),
            MockPosition(
                position_id=2,
                position_snapshot_id=100,
                fund_id=1,
                isin="US0378331005",
                quantity=Decimal("3000"),
                market_value=Decimal("300000.00"),
            ),
        ]

        instruments = {
            "IE00B4L5Y983": MockInstrument(
                isin="IE00B4L5Y983",
                asset_class="EQUITY",
                currency="EUR",
            ),
            "US0378331005": MockInstrument(
                isin="US0378331005",
                asset_class="EQUITY",
                currency="USD",
            ),
        }

        nav = Decimal("500000.00")

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=nav,
            positions=positions,
            instruments_by_isin=instruments,
            fx_rates={("USD", "EUR"): Decimal("0.92")},
        )

        # Total weight should be > 1.0 due to leverage
        assert portfolio.total_weight > Decimal("1.0")

    def test_multiple_positions_correct_totals(self) -> None:
        """Multiple positions sum to correct total weight."""
        enricher = self.make_enricher()

        positions = [
            MockPosition(
                position_id=1,
                position_snapshot_id=100,
                fund_id=1,
                isin="ISIN1",
                quantity=Decimal("1000"),
                market_value=Decimal("250000"),
            ),
            MockPosition(
                position_id=2,
                position_snapshot_id=100,
                fund_id=1,
                isin="ISIN2",
                quantity=Decimal("2000"),
                market_value=Decimal("250000"),
            ),
            MockPosition(
                position_id=3,
                position_snapshot_id=100,
                fund_id=1,
                isin="ISIN3",
                quantity=Decimal("3000"),
                market_value=Decimal("500000"),
            ),
        ]

        instruments = {
            "ISIN1": MockInstrument(
                isin="ISIN1",
                asset_class="EQUITY",
                currency="EUR",
            ),
            "ISIN2": MockInstrument(
                isin="ISIN2",
                asset_class="EQUITY",
                currency="EUR",
            ),
            "ISIN3": MockInstrument(
                isin="ISIN3",
                asset_class="EQUITY",
                currency="EUR",
            ),
        }

        nav = Decimal("1000000")  # Fully invested

        portfolio = enricher.enrich_portfolio(
            fund_id=1,
            fund_base_currency="EUR",
            valuation_date=date(2026, 6, 10),
            nav=nav,
            positions=positions,
            instruments_by_isin=instruments,
            fx_rates={},
        )

        # Total weight should be exactly 1.0 (fully invested)
        assert portfolio.total_weight == Decimal("1")
