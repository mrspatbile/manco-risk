"""Tests for enriched position models."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio


class TestEnrichedPosition:
    """Test EnrichedPosition model validation and construction."""

    def test_valid_enriched_position(self) -> None:
        """Create a valid enriched position."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="IE00B4L5Y983",
            valuation_date="2026-06-10",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("48000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.15"),
        )

        assert position.fund_id == 1
        assert position.weight == Decimal("0.15")
        assert position.market_value_base_ccy == Decimal("48000.00")

    def test_enriched_position_with_duration(self) -> None:
        """Create enriched position with optional duration."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="DE0001102309",
            valuation_date="2026-06-10",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="BOND",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.25"),
            modified_duration=Decimal("5.5"),
        )

        assert position.modified_duration == Decimal("5.5")

    def test_enriched_position_short_position(self) -> None:
        """Allow negative quantity for short positions."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="IE00B4L5Y983",
            valuation_date="2026-06-10",
            quantity=Decimal("-500"),  # Short position
            market_value=Decimal("25000.00"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("24000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.10"),
        )

        assert position.quantity == Decimal("-500")
        assert position.weight == Decimal("0.10")

    def test_enriched_position_zero_weight(self) -> None:
        """Allow zero weight (position closed or being unwound)."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="IE00B4L5Y983",
            valuation_date="2026-06-10",
            quantity=Decimal("0"),
            market_value=Decimal("0"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("0"),
            fund_base_currency="EUR",
            weight=Decimal("0"),
        )

        assert position.weight == Decimal("0")

    def test_enriched_position_currency_validation(self) -> None:
        """Currency codes must be uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=100,
                position_id=1001,
                isin="IE00B4L5Y983",
                valuation_date="2026-06-10",
                quantity=Decimal("1000"),
                market_value=Decimal("50000.00"),
                position_currency="usd",  # lowercase
                asset_class="EQUITY",
                instrument_currency="USD",
                market_value_base_ccy=Decimal("48000.00"),
                fund_base_currency="EUR",
                weight=Decimal("0.15"),
            )

        errors = exc_info.value.errors()
        assert any("uppercase" in str(e).lower() for e in errors)

    def test_enriched_position_negative_weight_rejected(self) -> None:
        """Negative weight is not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=100,
                position_id=1001,
                isin="IE00B4L5Y983",
                valuation_date="2026-06-10",
                quantity=Decimal("1000"),
                market_value=Decimal("50000.00"),
                position_currency="USD",
                asset_class="EQUITY",
                instrument_currency="USD",
                market_value_base_ccy=Decimal("48000.00"),
                fund_base_currency="EUR",
                weight=Decimal("-0.05"),  # negative
            )

        errors = exc_info.value.errors()
        assert any("non-negative" in str(e).lower() for e in errors)

    def test_enriched_position_negative_market_value_base_ccy_rejected(self) -> None:
        """Market value in base currency cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=100,
                position_id=1001,
                isin="IE00B4L5Y983",
                valuation_date="2026-06-10",
                quantity=Decimal("1000"),
                market_value=Decimal("50000.00"),
                position_currency="USD",
                asset_class="EQUITY",
                instrument_currency="USD",
                market_value_base_ccy=Decimal("-5000.00"),  # negative
                fund_base_currency="EUR",
                weight=Decimal("0.15"),
            )

        errors = exc_info.value.errors()
        assert any("non-negative" in str(e).lower() for e in errors)

    def test_enriched_position_negative_duration_rejected(self) -> None:
        """Modified duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=100,
                position_id=1001,
                isin="DE0001102309",
                valuation_date="2026-06-10",
                quantity=Decimal("500"),
                market_value=Decimal("100000.00"),
                position_currency="EUR",
                asset_class="BOND",
                instrument_currency="EUR",
                market_value_base_ccy=Decimal("100000.00"),
                fund_base_currency="EUR",
                weight=Decimal("0.25"),
                modified_duration=Decimal("-2.5"),  # negative
            )

        errors = exc_info.value.errors()
        assert any("non-negative" in str(e).lower() for e in errors)

    def test_enriched_position_with_spread_duration(self) -> None:
        """Bond position carries both modified_duration and spread_duration."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="XS2543791470",
            valuation_date="2026-06-10",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="BOND",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.25"),
            modified_duration=Decimal("4.71"),
            spread_duration=Decimal("4.71"),
        )
        assert position.modified_duration == Decimal("4.71")
        assert position.spread_duration == Decimal("4.71")

    def test_enriched_position_spread_duration_defaults_none(self) -> None:
        """spread_duration defaults to None when not provided."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="IE00B4L5Y983",
            valuation_date="2026-06-10",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("50000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.15"),
        )
        assert position.spread_duration is None

    def test_enriched_position_zero_spread_duration_valid(self) -> None:
        """spread_duration = 0.0 is valid (Phase 1 government bond convention)."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="US912828YK09",
            valuation_date="2026-06-10",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
            position_currency="USD",
            asset_class="BOND",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="USD",
            weight=Decimal("0.25"),
            modified_duration=Decimal("2.31"),
            spread_duration=Decimal("0.0"),
        )
        assert position.spread_duration == Decimal("0.0")

    def test_enriched_position_negative_spread_duration_rejected(self) -> None:
        """Negative spread_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPosition(
                fund_id=1,
                position_snapshot_id=100,
                position_id=1001,
                isin="XS2543791470",
                valuation_date="2026-06-10",
                quantity=Decimal("500"),
                market_value=Decimal("100000.00"),
                position_currency="EUR",
                asset_class="BOND",
                instrument_currency="EUR",
                market_value_base_ccy=Decimal("100000.00"),
                fund_base_currency="EUR",
                weight=Decimal("0.25"),
                spread_duration=Decimal("-1.0"),  # negative
            )

        errors = exc_info.value.errors()
        assert any("non-negative" in str(e).lower() for e in errors)

    def test_enriched_position_immutable(self) -> None:
        """EnrichedPosition is frozen (immutable)."""
        position = EnrichedPosition(
            fund_id=1,
            position_snapshot_id=100,
            position_id=1001,
            isin="IE00B4L5Y983",
            valuation_date="2026-06-10",
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("48000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.15"),
        )

        with pytest.raises(Exception):  # FrozenInstanceError in Pydantic v2
            position.weight = Decimal("0.20")  # type: ignore[misc]


class TestRiskReadyPortfolio:
    """Test RiskReadyPortfolio model validation and construction."""

    @staticmethod
    def make_position(
        fund_id: int = 1,
        position_id: int = 1001,
        valuation_date: str = "2026-06-10",
        fund_base_currency: str = "EUR",
        weight: Decimal = Decimal("0.15"),
    ) -> EnrichedPosition:
        """Helper to create a test position."""
        return EnrichedPosition(
            fund_id=fund_id,
            position_snapshot_id=100,
            position_id=position_id,
            isin="IE00B4L5Y983",
            valuation_date=valuation_date,
            quantity=Decimal("1000"),
            market_value=Decimal("50000.00"),
            position_currency="USD",
            asset_class="EQUITY",
            instrument_currency="USD",
            market_value_base_ccy=Decimal("48000.00"),
            fund_base_currency=fund_base_currency,
            weight=weight,
        )

    def test_valid_portfolio(self) -> None:
        """Create a valid portfolio."""
        positions = [
            self.make_position(position_id=1, weight=Decimal("0.40")),
            self.make_position(position_id=2, weight=Decimal("0.35")),
            self.make_position(position_id=3, weight=Decimal("0.25")),
        ]

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("1000000.00"),
            positions=positions,
        )

        assert portfolio.fund_id == 1
        assert len(portfolio.positions) == 3
        assert portfolio.total_weight == Decimal("1.00")

    def test_empty_portfolio(self) -> None:
        """Allow empty portfolio (no positions)."""
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[],
        )

        assert len(portfolio.positions) == 0
        assert portfolio.total_weight == Decimal("0")

    def test_portfolio_total_weight_property(self) -> None:
        """Total weight property sums all position weights."""
        positions = [
            self.make_position(position_id=1, weight=Decimal("0.50")),
            self.make_position(position_id=2, weight=Decimal("0.30")),
            self.make_position(position_id=3, weight=Decimal("0.15")),
        ]

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("1000000.00"),
            positions=positions,
        )

        assert portfolio.total_weight == Decimal("0.95")

    def test_portfolio_leveraged(self) -> None:
        """Portfolio with total weight > 1.0 (leveraged)."""
        positions = [
            self.make_position(position_id=1, weight=Decimal("0.70")),
            self.make_position(position_id=2, weight=Decimal("0.50")),
        ]

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("1000000.00"),
            positions=positions,
        )

        assert portfolio.total_weight == Decimal("1.20")

    def test_portfolio_nav_validation(self) -> None:
        """NAV must be strictly positive."""
        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("0"),  # Invalid: zero NAV
                positions=[],
            )

        errors = exc_info.value.errors()
        assert any("strictly positive" in str(e).lower() for e in errors)

    def test_portfolio_nav_negative_rejected(self) -> None:
        """NAV must be strictly positive (negative rejected)."""
        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("-100000.00"),  # Invalid: negative NAV
                positions=[],
            )

        errors = exc_info.value.errors()
        assert any("strictly positive" in str(e).lower() for e in errors)

    def test_portfolio_currency_validation(self) -> None:
        """Fund base currency must be uppercase."""
        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="eur",  # lowercase
                nav=Decimal("1000000.00"),
                positions=[],
            )

        errors = exc_info.value.errors()
        assert any("uppercase" in str(e).lower() for e in errors)

    def test_portfolio_position_fund_id_mismatch(self) -> None:
        """All positions must match portfolio fund_id."""
        position_wrong_fund = self.make_position(fund_id=99)  # Different fund

        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("1000000.00"),
                positions=[position_wrong_fund],
            )

        errors = exc_info.value.errors()
        assert any("fund_id" in str(e).lower() for e in errors)

    def test_portfolio_position_valuation_date_mismatch(self) -> None:
        """All positions must match portfolio valuation_date."""
        position_wrong_date = self.make_position(valuation_date="2026-06-09")

        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("1000000.00"),
                positions=[position_wrong_date],
            )

        errors = exc_info.value.errors()
        assert any("valuation_date" in str(e).lower() for e in errors)

    def test_portfolio_position_currency_mismatch(self) -> None:
        """All positions must match portfolio fund_base_currency."""
        position_wrong_ccy = self.make_position(fund_base_currency="USD")

        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("1000000.00"),
                positions=[position_wrong_ccy],
            )

        errors = exc_info.value.errors()
        assert any("fund_base_currency" in str(e).lower() for e in errors)

    def test_portfolio_multiple_positions_consistency(self) -> None:
        """All positions must be consistent when multiple present."""
        positions = [
            self.make_position(position_id=1),
            self.make_position(position_id=2),
            self.make_position(position_id=3, fund_id=99),  # Third one has wrong fund
        ]

        with pytest.raises(ValidationError) as exc_info:
            RiskReadyPortfolio(
                fund_id=1,
                valuation_date="2026-06-10",
                fund_base_currency="EUR",
                nav=Decimal("1000000.00"),
                positions=positions,
            )

        errors = exc_info.value.errors()
        assert any("fund_id" in str(e).lower() for e in errors)

    def test_portfolio_immutable(self) -> None:
        """RiskReadyPortfolio is frozen (immutable)."""
        positions = [self.make_position()]

        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="EUR",
            nav=Decimal("1000000.00"),
            positions=positions,
        )

        with pytest.raises(Exception):  # FrozenInstanceError in Pydantic v2
            portfolio.nav = Decimal("2000000.00")  # type: ignore[misc]
