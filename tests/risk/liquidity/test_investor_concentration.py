"""Tests for investor concentration domain models and engine.

Tests investor holding models, concentration results, and analysis calculations.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.liquidity import (
    InvestorConcentrationEngine,
    InvestorConcentrationResult,
    InvestorHolding,
    TopNInvestor,
)


class TestInvestorHolding:
    def test_valid_holding(self):
        """Valid investor holding."""
        holding = InvestorHolding(
            investor_id="INV001",
            nav_amount=Decimal("500000"),
        )
        assert holding.investor_id == "INV001"
        assert holding.nav_amount == Decimal("500000")

    def test_zero_holding_valid(self):
        """Zero holding is valid."""
        holding = InvestorHolding(
            investor_id="INV001",
            nav_amount=Decimal("0"),
        )
        assert holding.nav_amount == Decimal("0")

    def test_empty_investor_id_raises(self):
        """Empty investor ID raises ValueError."""
        with pytest.raises(ValueError, match="investor_id must be non-empty"):
            InvestorHolding(
                investor_id="",
                nav_amount=Decimal("500000"),
            )

    def test_negative_nav_amount_raises(self):
        """Negative NAV amount raises ValueError."""
        with pytest.raises(ValueError, match="nav_amount must be non-negative"):
            InvestorHolding(
                investor_id="INV001",
                nav_amount=Decimal("-1000"),
            )


class TestTopNInvestor:
    def test_valid_top_n_investor(self):
        """Valid top-N investor."""
        investor = TopNInvestor(
            investor_id="INV001",
            total_amount=Decimal("500000"),
            percentage_of_nav=Decimal("0.25"),
        )
        assert investor.investor_id == "INV001"
        assert investor.percentage_of_nav == Decimal("0.25")

    def test_zero_percentage_valid(self):
        """Zero percentage is valid."""
        investor = TopNInvestor(
            investor_id="INV001",
            total_amount=Decimal("0"),
            percentage_of_nav=Decimal("0"),
        )
        assert investor.percentage_of_nav == Decimal("0")

    def test_100_percent_valid(self):
        """100% (sole investor) is valid."""
        investor = TopNInvestor(
            investor_id="INV001",
            total_amount=Decimal("2000000"),
            percentage_of_nav=Decimal("1"),
        )
        assert investor.percentage_of_nav == Decimal("1")

    def test_percentage_greater_than_one_raises(self):
        """Percentage > 100% raises ValueError."""
        with pytest.raises(ValueError, match="percentage_of_nav must be in range"):
            TopNInvestor(
                investor_id="INV001",
                total_amount=Decimal("500000"),
                percentage_of_nav=Decimal("1.1"),
            )


class TestInvestorConcentrationResult:
    def test_valid_result(self):
        """Valid concentration result."""
        top_1_investor = [
            TopNInvestor(
                investor_id="INV001",
                total_amount=Decimal("1000000"),
                percentage_of_nav=Decimal("0.5"),
            )
        ]
        result = InvestorConcentrationResult(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            total_investor_count=4,
            largest_investor_id="INV001",
            largest_investor_amount=Decimal("1000000"),
            largest_investor_percentage=Decimal("0.5"),
            top_n_levels=[1, 5],
            top_n_investors={1: top_1_investor, 5: top_1_investor},
        )
        assert result.fund_nav == Decimal("2000000")
        assert result.total_investor_count == 4

    def test_zero_fund_nav_raises(self):
        """Zero fund NAV raises ValueError."""
        with pytest.raises(ValueError, match="fund_nav must be positive"):
            InvestorConcentrationResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("0"),
                total_investor_count=1,
                largest_investor_id="INV001",
                largest_investor_amount=Decimal("0"),
                largest_investor_percentage=Decimal("0"),
                top_n_levels=[1],
                top_n_investors={1: []},
            )

    def test_negative_fund_nav_raises(self):
        """Negative fund NAV raises ValueError."""
        with pytest.raises(ValueError, match="fund_nav must be positive"):
            InvestorConcentrationResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("-1000000"),
                total_investor_count=1,
                largest_investor_id="INV001",
                largest_investor_amount=Decimal("0"),
                largest_investor_percentage=Decimal("0"),
                top_n_levels=[1],
                top_n_investors={1: []},
            )

    def test_empty_top_n_levels_raises(self):
        """Empty top_n_levels raises ValueError."""
        with pytest.raises(ValueError, match="top_n_levels must contain"):
            InvestorConcentrationResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("2000000"),
                total_investor_count=1,
                largest_investor_id="INV001",
                largest_investor_amount=Decimal("2000000"),
                largest_investor_percentage=Decimal("1"),
                top_n_levels=[],
                top_n_investors={},
            )

    def test_negative_top_n_level_raises(self):
        """Negative top-N level raises ValueError."""
        with pytest.raises(ValueError, match="top_n_levels must contain positive"):
            InvestorConcentrationResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("2000000"),
                total_investor_count=1,
                largest_investor_id="INV001",
                largest_investor_amount=Decimal("2000000"),
                largest_investor_percentage=Decimal("1"),
                top_n_levels=[1, -5],
                top_n_investors={1: []},
            )

    def test_top_n_size_exceeds_level_raises(self):
        """Top-N list with more investors than N raises ValueError."""
        investors = [
            TopNInvestor(
                investor_id="INV001",
                total_amount=Decimal("1000000"),
                percentage_of_nav=Decimal("0.5"),
            ),
            TopNInvestor(
                investor_id="INV002",
                total_amount=Decimal("500000"),
                percentage_of_nav=Decimal("0.25"),
            ),
        ]
        with pytest.raises(ValueError, match="top-1 has 2 investors"):
            InvestorConcentrationResult(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("2000000"),
                total_investor_count=2,
                largest_investor_id="INV001",
                largest_investor_amount=Decimal("1000000"),
                largest_investor_percentage=Decimal("0.5"),
                top_n_levels=[1],
                top_n_investors={1: investors},
            )


class TestInvestorConcentrationEngine:
    @pytest.fixture
    def diversified_portfolio(self):
        """Diversified investor base."""
        return [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("500000")),
            InvestorHolding(investor_id="INV002", nav_amount=Decimal("300000")),
            InvestorHolding(investor_id="INV003", nav_amount=Decimal("200000")),
            InvestorHolding(investor_id="INV004", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV005", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV006", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV007", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV008", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV009", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV010", nav_amount=Decimal("100000")),
        ]

    def test_normal_diversified_calculation(self, diversified_portfolio):
        """Normal concentration calculation on diversified portfolio."""
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=diversified_portfolio,
            top_n_levels=[1, 5, 10],
        )

        assert result.fund_id == 1
        assert result.fund_nav == Decimal("2000000")
        assert result.total_investor_count == 10
        assert result.largest_investor_id == "INV001"
        assert result.largest_investor_amount == Decimal("500000")
        assert result.largest_investor_percentage == Decimal("0.25")

    def test_top_1_concentration(self, diversified_portfolio):
        """Top-1 investor concentration."""
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=diversified_portfolio,
            top_n_levels=[1],
        )

        assert len(result.top_n_investors[1]) == 1
        assert result.top_n_investors[1][0].investor_id == "INV001"
        assert result.top_n_investors[1][0].total_amount == Decimal("500000")

    def test_top_5_concentration(self, diversified_portfolio):
        """Top-5 investor concentration."""
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=diversified_portfolio,
            top_n_levels=[5],
        )

        assert len(result.top_n_investors[5]) == 5
        assert result.top_n_investors[5][0].investor_id == "INV001"
        assert result.top_n_investors[5][1].investor_id == "INV002"

    def test_top_10_concentration(self, diversified_portfolio):
        """Top-10 investor concentration."""
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=diversified_portfolio,
            top_n_levels=[10],
        )

        assert len(result.top_n_investors[10]) == 10

    def test_fewer_investors_than_top_n(self):
        """Request top-20 but only 5 investors exist."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
            InvestorHolding(investor_id="INV002", nav_amount=Decimal("500000")),
            InvestorHolding(investor_id="INV003", nav_amount=Decimal("300000")),
            InvestorHolding(investor_id="INV004", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV005", nav_amount=Decimal("100000")),
        ]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=holdings,
            top_n_levels=[10, 20],
        )

        assert len(result.top_n_investors[10]) == 5
        assert len(result.top_n_investors[20]) == 5

    def test_single_investor_concentration(self):
        """Single large investor (sole investor)."""
        holdings = [InvestorHolding(investor_id="INV001", nav_amount=Decimal("5000000"))]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("5000000"),
            investor_holdings=holdings,
            top_n_levels=[1],
        )

        assert result.largest_investor_id == "INV001"
        assert result.largest_investor_percentage == Decimal("1")

    def test_zero_holding_valid(self):
        """Zero holding for an investor is valid."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("2000000")),
            InvestorHolding(investor_id="INV002", nav_amount=Decimal("0")),
        ]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("2000000"),
            investor_holdings=holdings,
            top_n_levels=[1, 2],
        )

        assert result.total_investor_count == 2
        assert result.top_n_investors[2][1].investor_id == "INV002"

    def test_duplicate_investor_id_raises(self):
        """Duplicate investor IDs raise ValueError."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("500000")),
        ]
        engine = InvestorConcentrationEngine()
        with pytest.raises(ValueError, match="Duplicate investor IDs"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("1500000"),
                investor_holdings=holdings,
                top_n_levels=[1],
            )

    def test_no_investors_raises(self):
        """Empty investor holdings raise ValueError."""
        engine = InvestorConcentrationEngine()
        with pytest.raises(ValueError, match="investor_holdings must contain"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("1000000"),
                investor_holdings=[],
                top_n_levels=[1],
            )

    def test_holdings_exceed_nav_raises(self):
        """Total holdings > NAV (materially) raise ValueError."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
            InvestorHolding(investor_id="INV002", nav_amount=Decimal("500000")),
            InvestorHolding(investor_id="INV003", nav_amount=Decimal("600000")),
        ]
        engine = InvestorConcentrationEngine()
        with pytest.raises(ValueError, match="exceeds fund NAV"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("2000000"),  # Holdings sum to 2.1M
                investor_holdings=holdings,
                top_n_levels=[1],
            )

    def test_empty_top_n_levels_raises(self):
        """Empty top_n_levels raise ValueError."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
        ]
        engine = InvestorConcentrationEngine()
        with pytest.raises(ValueError, match="top_n_levels must not be empty"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("1000000"),
                investor_holdings=holdings,
                top_n_levels=[],
            )

    def test_negative_top_n_level_raises(self):
        """Negative top-N level raises ValueError."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
        ]
        engine = InvestorConcentrationEngine()
        with pytest.raises(ValueError, match="top_n_levels must contain positive"):
            engine.calculate(
                fund_id=1,
                valuation_date=date(2026, 6, 30),
                fund_nav=Decimal("1000000"),
                investor_holdings=holdings,
                top_n_levels=[1, -5],
            )

    def test_preserves_metadata(self):
        """Result preserves fund ID and valuation date."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("1000000")),
        ]
        engine = InvestorConcentrationEngine()
        fund_id = 42
        val_date = date(2026, 3, 15)
        result = engine.calculate(
            fund_id=fund_id,
            valuation_date=val_date,
            fund_nav=Decimal("1000000"),
            investor_holdings=holdings,
            top_n_levels=[1],
        )

        assert result.fund_id == fund_id
        assert result.valuation_date == val_date

    def test_sorted_descending_by_holding(self):
        """Investors sorted by holding amount descending."""
        holdings = [
            InvestorHolding(investor_id="INV001", nav_amount=Decimal("100000")),
            InvestorHolding(investor_id="INV002", nav_amount=Decimal("500000")),
            InvestorHolding(investor_id="INV003", nav_amount=Decimal("300000")),
        ]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("900000"),
            investor_holdings=holdings,
            top_n_levels=[3],
        )

        assert result.top_n_investors[3][0].investor_id == "INV002"  # 500k
        assert result.top_n_investors[3][1].investor_id == "INV003"  # 300k
        assert result.top_n_investors[3][2].investor_id == "INV001"  # 100k


class TestInvestorConcentrationIntegration:
    """Integration tests with realistic scenarios."""

    def test_large_fund_many_small_investors(self):
        """Large fund with many small retail investors."""
        holdings = [
            InvestorHolding(investor_id=f"RETAIL_{i:04d}", nav_amount=Decimal("10000"))
            for i in range(100)
        ]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("1000000"),
            investor_holdings=holdings,
            top_n_levels=[1, 5, 10],
        )

        assert result.total_investor_count == 100
        assert result.largest_investor_percentage == Decimal("0.01")
        assert len(result.top_n_investors[5]) == 5
        assert len(result.top_n_investors[10]) == 10

    def test_concentrated_fund_few_large_investors(self):
        """Concentrated fund with few large institutional investors."""
        holdings = [
            InvestorHolding(investor_id="INST_001", nav_amount=Decimal("3000000")),
            InvestorHolding(investor_id="INST_002", nav_amount=Decimal("2000000")),
            InvestorHolding(investor_id="INST_003", nav_amount=Decimal("1500000")),
            InvestorHolding(investor_id="INST_004", nav_amount=Decimal("1000000")),
            InvestorHolding(investor_id="RETAIL_001", nav_amount=Decimal("500000")),
            InvestorHolding(investor_id="RETAIL_002", nav_amount=Decimal("500000")),
        ]
        engine = InvestorConcentrationEngine()
        result = engine.calculate(
            fund_id=1,
            valuation_date=date(2026, 6, 30),
            fund_nav=Decimal("8500000"),
            investor_holdings=holdings,
            top_n_levels=[1, 3],
        )

        assert result.largest_investor_percentage > Decimal("0.3")
        top_3_total = sum(inv.total_amount for inv in result.top_n_investors[3])
        assert top_3_total == Decimal("6500000")
