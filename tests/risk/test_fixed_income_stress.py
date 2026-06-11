"""Tests for fixed-income stress testing models and duration-based pricer.

Covers:
- FixedIncomeStressScenario model validation
- FixedIncomeStressInput model validation
- FixedIncomeStressPositionResult model validation
- FixedIncomeStressPortfolioResult model validation
- DurationBasedFixedIncomePricer arithmetic and error handling

Methodology (DurationBasedFixedIncomePricer):
    rate_shock_decimal   = rate_shock_bps / 10_000
    spread_shock_decimal = spread_shock_bps / 10_000
    rate_pnl   = -modified_duration * rate_shock_decimal * dirty_value
    credit_pnl = -spread_duration   * spread_shock_decimal * dirty_value
    total_pnl  = rate_pnl + credit_pnl

Dirty value convention:
    current_dirty_value_base_ccy == market_value_base_ccy from EnrichedPosition.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.duration_based_pricer import DurationBasedFixedIncomePricer
from manco_risk.risk.engines.fixed_income_stress import FixedIncomeStressEngine
from manco_risk.risk.exceptions import MissingDurationError, UnsupportedAssetClassError
from manco_risk.risk.models.fixed_income_stress_input import FixedIncomeStressInput
from manco_risk.risk.models.fixed_income_stress_portfolio_result import (
    FixedIncomeStressPortfolioResult,
)
from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_bond_position(
    position_id: int = 1,
    isin: str = "US912828YK09",
    market_value_base_ccy: Decimal = Decimal("100000"),
    modified_duration: Decimal | None = Decimal("4.0"),
    spread_duration: Decimal | None = Decimal("4.0"),
    fund_base_currency: str = "USD",
) -> EnrichedPosition:
    """Return a minimal BOND enriched position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=Decimal("1000"),
        market_value=market_value_base_ccy,
        position_currency=fund_base_currency,
        asset_class="BOND",
        instrument_currency=fund_base_currency,
        market_value_base_ccy=market_value_base_ccy,
        fund_base_currency=fund_base_currency,
        weight=Decimal("1.0"),
        modified_duration=modified_duration,
        spread_duration=spread_duration,
    )


def make_scenario(
    scenario_id: str = "FI_RATE_UP_100",
    shock_type: str = "RATE_SHOCK",
    rate_shock_bps: int = 100,
    spread_shock_bps: int = 0,
) -> FixedIncomeStressScenario:
    """Return a minimal fixed-income stress scenario."""
    return FixedIncomeStressScenario(
        scenario_id=scenario_id,
        scenario_name="Rate up 100 bps",
        scenario_type="HYPOTHETICAL",
        scenario_source="MANAGER_DEFINED",
        shock_type=shock_type,
        rate_shock_bps=rate_shock_bps,
        spread_shock_bps=spread_shock_bps,
        description="Parallel yield curve shift up by 100 bps.",
    )


def make_position_result(
    rate_pnl: Decimal = Decimal("-4000"),
    credit_pnl: Decimal = Decimal("0"),
    total_pnl: Decimal = Decimal("-4000"),
    stressed_dirty_value: Decimal = Decimal("96000"),
) -> FixedIncomeStressPositionResult:
    """Return a minimal FixedIncomeStressPositionResult."""
    return FixedIncomeStressPositionResult(
        position_id=1,
        isin="US912828YK09",
        asset_class="BOND",
        shock_type="RATE_SHOCK",
        rate_shock_bps=100,
        spread_shock_bps=0,
        modified_duration=Decimal("4.0"),
        spread_duration=None,
        current_dirty_value_base_ccy=Decimal("100000"),
        stressed_dirty_value_base_ccy=stressed_dirty_value,
        rate_pnl=rate_pnl,
        credit_pnl=credit_pnl,
        total_pnl=total_pnl,
    )


# ---------------------------------------------------------------------------
# Model tests: FixedIncomeStressScenario
# ---------------------------------------------------------------------------


class TestFixedIncomeStressScenario:
    def test_valid_rate_shock_scenario(self) -> None:
        scenario = make_scenario()
        assert scenario.scenario_id == "FI_RATE_UP_100"
        assert scenario.rate_shock_bps == 100
        assert scenario.spread_shock_bps == 0

    def test_valid_spread_shock_scenario(self) -> None:
        scenario = make_scenario(
            scenario_id="FI_SPREAD_UP_50",
            shock_type="SPREAD_SHOCK",
            rate_shock_bps=0,
            spread_shock_bps=50,
        )
        assert scenario.spread_shock_bps == 50
        assert scenario.rate_shock_bps == 0

    def test_valid_combined_scenario(self) -> None:
        scenario = make_scenario(
            scenario_id="FI_COMBINED",
            shock_type="COMBINED",
            rate_shock_bps=100,
            spread_shock_bps=50,
        )
        assert scenario.shock_type == "COMBINED"
        assert scenario.rate_shock_bps == 100
        assert scenario.spread_shock_bps == 50

    def test_bps_stored_as_int(self) -> None:
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=50)
        assert isinstance(scenario.rate_shock_bps, int)
        assert isinstance(scenario.spread_shock_bps, int)

    def test_negative_rate_shock_valid(self) -> None:
        scenario = make_scenario(rate_shock_bps=-50)
        assert scenario.rate_shock_bps == -50

    def test_empty_scenario_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressScenario(
                scenario_id="",
                scenario_name="Name",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="RATE_SHOCK",
                rate_shock_bps=100,
                spread_shock_bps=0,
                description="desc",
            )

    def test_empty_description_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressScenario(
                scenario_id="ID",
                scenario_name="Name",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="RATE_SHOCK",
                rate_shock_bps=100,
                spread_shock_bps=0,
                description="   ",
            )

    def test_shock_type_is_free_form_string(self) -> None:
        """shock_type is an audit label — any non-empty string is accepted."""
        scenario = make_scenario(shock_type="MY_CUSTOM_SHOCK")
        assert scenario.shock_type == "MY_CUSTOM_SHOCK"

    def test_scenario_frozen(self) -> None:
        scenario = make_scenario()
        with pytest.raises(Exception):
            scenario.rate_shock_bps = 200  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Model tests: FixedIncomeStressInput
# ---------------------------------------------------------------------------


class TestFixedIncomeStressInput:
    def test_valid_input(self) -> None:
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="USD",
            nav=Decimal("1000000"),
            positions=[],
        )
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[make_scenario()],
        )
        assert len(fi_input.scenarios) == 1

    def test_empty_scenarios_rejected(self) -> None:
        portfolio = RiskReadyPortfolio(
            fund_id=1,
            valuation_date="2026-06-10",
            fund_base_currency="USD",
            nav=Decimal("1000000"),
            positions=[],
        )
        with pytest.raises(ValidationError) as exc_info:
            FixedIncomeStressInput(portfolio=portfolio, scenarios=[])
        assert "empty" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Model tests: FixedIncomeStressPositionResult
# ---------------------------------------------------------------------------


class TestFixedIncomeStressPositionResult:
    def test_valid_result(self) -> None:
        result = make_position_result()
        assert result.position_id == 1
        assert result.rate_pnl == Decimal("-4000")
        assert result.credit_pnl == Decimal("0")
        assert result.total_pnl == Decimal("-4000")

    def test_negative_current_dirty_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressPositionResult(
                position_id=1,
                isin="US912828YK09",
                asset_class="BOND",
                shock_type="RATE_SHOCK",
                rate_shock_bps=100,
                spread_shock_bps=0,
                current_dirty_value_base_ccy=Decimal("-1"),  # invalid
                stressed_dirty_value_base_ccy=Decimal("96000"),
                rate_pnl=Decimal("-4000"),
                credit_pnl=Decimal("0"),
                total_pnl=Decimal("-4000"),
            )

    def test_empty_shock_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressPositionResult(
                position_id=1,
                isin="US912828YK09",
                asset_class="BOND",
                shock_type="",  # invalid
                rate_shock_bps=100,
                spread_shock_bps=0,
                current_dirty_value_base_ccy=Decimal("100000"),
                stressed_dirty_value_base_ccy=Decimal("96000"),
                rate_pnl=Decimal("-4000"),
                credit_pnl=Decimal("0"),
                total_pnl=Decimal("-4000"),
            )

    def test_position_name_optional(self) -> None:
        result = make_position_result()
        assert result.position_name is None

    def test_result_frozen(self) -> None:
        result = make_position_result()
        with pytest.raises(Exception):
            result.rate_pnl = Decimal("0")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Model tests: FixedIncomeStressPortfolioResult
# ---------------------------------------------------------------------------


class TestFixedIncomeStressPortfolioResult:
    def test_valid_portfolio_result(self) -> None:
        pos_result = make_position_result()
        result = FixedIncomeStressPortfolioResult(
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            scenario_id="FI_RATE_UP_100",
            scenario_name="Rate up 100 bps",
            scenario_type="HYPOTHETICAL",
            scenario_source="MANAGER_DEFINED",
            shock_type="RATE_SHOCK",
            rate_shock_bps=100,
            spread_shock_bps=0,
            current_nav=Decimal("100000"),
            stressed_nav=Decimal("96000"),
            total_rate_pnl=Decimal("-4000"),
            total_credit_pnl=Decimal("0"),
            total_pnl=Decimal("-4000"),
            loss_pct_nav=Decimal("0.04"),
            stressed_positions=[pos_result],
            num_bond_positions=1,
            num_cash_positions=0,
        )
        assert result.loss_pct_nav == Decimal("0.04")
        assert result.total_pnl == Decimal("-4000")
        assert result.num_bond_positions == 1

    def test_negative_nav_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressPortfolioResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                scenario_id="ID",
                scenario_name="Name",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="RATE_SHOCK",
                rate_shock_bps=100,
                spread_shock_bps=0,
                current_nav=Decimal("-1"),  # invalid
                stressed_nav=Decimal("96000"),
                total_rate_pnl=Decimal("-4000"),
                total_credit_pnl=Decimal("0"),
                total_pnl=Decimal("-4000"),
                loss_pct_nav=Decimal("0.04"),
                stressed_positions=[],
                num_bond_positions=0,
                num_cash_positions=0,
            )

    def test_negative_loss_pct_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FixedIncomeStressPortfolioResult(
                fund_id=1,
                valuation_date=date(2026, 6, 10),
                scenario_id="ID",
                scenario_name="Name",
                scenario_type="HYPOTHETICAL",
                scenario_source="MANAGER_DEFINED",
                shock_type="RATE_SHOCK",
                rate_shock_bps=100,
                spread_shock_bps=0,
                current_nav=Decimal("100000"),
                stressed_nav=Decimal("104000"),
                total_rate_pnl=Decimal("4000"),
                total_credit_pnl=Decimal("0"),
                total_pnl=Decimal("4000"),
                loss_pct_nav=Decimal("-0.04"),  # invalid
                stressed_positions=[],
                num_bond_positions=1,
                num_cash_positions=0,
            )


# ---------------------------------------------------------------------------
# Pricer tests: DurationBasedFixedIncomePricer
# ---------------------------------------------------------------------------


class TestDurationBasedFixedIncomePricer:
    @staticmethod
    def make_pricer() -> DurationBasedFixedIncomePricer:
        return DurationBasedFixedIncomePricer()

    # --- Arithmetic ---

    def test_rate_shock_arithmetic(self) -> None:
        """rate_pnl = -modified_duration * (rate_shock_bps/10000) * dirty_value."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)

        # -4.0 * (100/10000) * 100000 = -4.0 * 0.01 * 100000 = -4000
        assert result.rate_pnl == Decimal("-4000")
        assert result.credit_pnl == Decimal("0")
        assert result.total_pnl == Decimal("-4000")

    def test_spread_shock_arithmetic(self) -> None:
        """credit_pnl = -spread_duration * (spread_shock_bps/10000) * dirty_value."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=None,
            spread_duration=Decimal("4.71"),
        )
        scenario = make_scenario(shock_type="SPREAD_SHOCK", rate_shock_bps=0, spread_shock_bps=50)

        result = pricer.price_position(position, scenario)

        # -4.71 * (50/10000) * 100000 = -4.71 * 0.005 * 100000 = -2355
        expected_credit_pnl = -(
            Decimal("4.71") * Decimal("50") / Decimal("10000") * Decimal("100000")
        )
        assert result.credit_pnl == expected_credit_pnl
        assert result.rate_pnl == Decimal("0")
        assert result.total_pnl == expected_credit_pnl

    def test_combined_shock_arithmetic(self) -> None:
        """Combined scenario: total_pnl = rate_pnl + credit_pnl."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("4.0"),
        )
        scenario = make_scenario(
            scenario_id="FI_COMBINED",
            shock_type="COMBINED",
            rate_shock_bps=100,
            spread_shock_bps=50,
        )

        result = pricer.price_position(position, scenario)

        expected_rate_pnl = -(
            Decimal("4.0") * Decimal("100") / Decimal("10000") * Decimal("100000")
        )
        expected_credit_pnl = -(
            Decimal("4.0") * Decimal("50") / Decimal("10000") * Decimal("100000")
        )
        expected_total = expected_rate_pnl + expected_credit_pnl

        assert result.rate_pnl == expected_rate_pnl
        assert result.credit_pnl == expected_credit_pnl
        assert result.total_pnl == expected_total

    def test_decomposed_pnl_sums_to_total(self) -> None:
        """rate_pnl + credit_pnl == total_pnl for any combined scenario."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("250000"),
            modified_duration=Decimal("7.5"),
            spread_duration=Decimal("6.8"),
        )
        scenario = make_scenario(shock_type="COMBINED", rate_shock_bps=75, spread_shock_bps=30)

        result = pricer.price_position(position, scenario)
        assert result.rate_pnl + result.credit_pnl == result.total_pnl

    # --- Government bond (zero spread duration) ---

    def test_government_bond_zero_spread_duration_gives_zero_credit_pnl(self) -> None:
        """spread_duration=0 gives credit_pnl=0 regardless of spread_shock_bps."""
        pricer = self.make_pricer()
        position = make_bond_position(
            modified_duration=Decimal("2.31"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(shock_type="COMBINED", rate_shock_bps=100, spread_shock_bps=50)

        result = pricer.price_position(position, scenario)
        assert result.credit_pnl == Decimal("0")

    # --- Missing duration errors ---

    def test_missing_modified_duration_with_nonzero_rate_shock_raises(self) -> None:
        """MissingDurationError when modified_duration is None and rate_shock_bps != 0."""
        pricer = self.make_pricer()
        position = make_bond_position(modified_duration=None, spread_duration=Decimal("4.0"))
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        with pytest.raises(MissingDurationError) as exc_info:
            pricer.price_position(position, scenario)

        assert exc_info.value.field == "modified_duration"
        assert exc_info.value.isin == position.isin

    def test_missing_spread_duration_with_nonzero_spread_shock_raises(self) -> None:
        """MissingDurationError when spread_duration is None and spread_shock_bps != 0."""
        pricer = self.make_pricer()
        position = make_bond_position(modified_duration=Decimal("4.0"), spread_duration=None)
        scenario = make_scenario(shock_type="SPREAD_SHOCK", rate_shock_bps=0, spread_shock_bps=50)

        with pytest.raises(MissingDurationError) as exc_info:
            pricer.price_position(position, scenario)

        assert exc_info.value.field == "spread_duration"
        assert exc_info.value.isin == position.isin

    # --- Zero bps exemption ---

    def test_zero_rate_shock_with_missing_modified_duration_no_error(self) -> None:
        """rate_shock_bps=0 does not require modified_duration."""
        pricer = self.make_pricer()
        position = make_bond_position(modified_duration=None, spread_duration=Decimal("4.0"))
        scenario = make_scenario(shock_type="SPREAD_SHOCK", rate_shock_bps=0, spread_shock_bps=50)

        result = pricer.price_position(position, scenario)
        assert result.rate_pnl == Decimal("0")

    def test_zero_spread_shock_with_missing_spread_duration_no_error(self) -> None:
        """spread_shock_bps=0 does not require spread_duration."""
        pricer = self.make_pricer()
        position = make_bond_position(modified_duration=Decimal("4.0"), spread_duration=None)
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)
        assert result.credit_pnl == Decimal("0")

    # --- Sign conventions ---

    def test_positive_rate_shock_gives_negative_rate_pnl(self) -> None:
        """Yield up (positive bps) → bond price falls → negative rate P&L (loss)."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("5.0"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)
        assert result.rate_pnl < Decimal("0")

    def test_negative_rate_shock_gives_positive_rate_pnl(self) -> None:
        """Yield down (negative bps) → bond price rises → positive rate P&L (gain)."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("5.0"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(rate_shock_bps=-50, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)
        assert result.rate_pnl > Decimal("0")

    def test_positive_spread_shock_gives_negative_credit_pnl(self) -> None:
        """Spread widening (positive bps) → bond price falls → negative credit P&L (loss)."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=None,
            spread_duration=Decimal("4.71"),
        )
        scenario = make_scenario(shock_type="SPREAD_SHOCK", rate_shock_bps=0, spread_shock_bps=50)

        result = pricer.price_position(position, scenario)
        assert result.credit_pnl < Decimal("0")

    # --- Decimal precision ---

    def test_decimal_precision_preserved(self) -> None:
        """P&L calculation does not lose Decimal precision."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("123456.789"),
            modified_duration=Decimal("3.14159"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)

        expected = -(Decimal("3.14159") * Decimal("100") / Decimal("10000") * Decimal("123456.789"))
        assert result.rate_pnl == expected

    # --- Dirty value proxy ---

    def test_current_dirty_value_equals_market_value_base_ccy(self) -> None:
        """current_dirty_value_base_ccy == market_value_base_ccy from EnrichedPosition."""
        pricer = self.make_pricer()
        mv = Decimal("87654.32")
        position = make_bond_position(
            market_value_base_ccy=mv,
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("0"),
        )
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)
        assert result.current_dirty_value_base_ccy == mv

    def test_stressed_dirty_value_equals_dirty_plus_total_pnl(self) -> None:
        """stressed_dirty_value = current_dirty_value + total_pnl."""
        pricer = self.make_pricer()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("2.0"),
        )
        scenario = make_scenario(shock_type="COMBINED", rate_shock_bps=100, spread_shock_bps=50)

        result = pricer.price_position(position, scenario)
        assert result.stressed_dirty_value_base_ccy == (
            result.current_dirty_value_base_ccy + result.total_pnl
        )

    # --- Metadata propagation ---

    def test_scenario_metadata_propagated_to_result(self) -> None:
        """shock_type and bps values from scenario appear in position result."""
        pricer = self.make_pricer()
        position = make_bond_position(
            modified_duration=Decimal("4.0"), spread_duration=Decimal("4.0")
        )
        scenario = make_scenario(shock_type="COMBINED", rate_shock_bps=75, spread_shock_bps=30)

        result = pricer.price_position(position, scenario)
        assert result.shock_type == "COMBINED"
        assert result.rate_shock_bps == 75
        assert result.spread_shock_bps == 30

    def test_position_id_and_isin_propagated(self) -> None:
        """position_id and isin from EnrichedPosition appear in result."""
        pricer = self.make_pricer()
        position = make_bond_position(
            position_id=42,
            isin="XS2543791470",
            modified_duration=Decimal("4.71"),
            spread_duration=Decimal("4.71"),
        )
        scenario = make_scenario(rate_shock_bps=100, spread_shock_bps=0)

        result = pricer.price_position(position, scenario)
        assert result.position_id == 42
        assert result.isin == "XS2543791470"


# ---------------------------------------------------------------------------
# Engine tests: FixedIncomeStressEngine
# ---------------------------------------------------------------------------


def make_cash_position(
    position_id: int = 99,
    isin: str = "CASH_USD",
    market_value_base_ccy: Decimal = Decimal("20000"),
    fund_base_currency: str = "USD",
    instrument_currency: str = "USD",
) -> EnrichedPosition:
    """Return a base-currency CASH enriched position."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=market_value_base_ccy,
        market_value=market_value_base_ccy,
        position_currency=instrument_currency,
        asset_class="CASH",
        instrument_currency=instrument_currency,
        market_value_base_ccy=market_value_base_ccy,
        fund_base_currency=fund_base_currency,
        weight=Decimal("0.2"),
    )


def make_equity_position(
    position_id: int = 50,
    isin: str = "US0378331005",
    market_value_base_ccy: Decimal = Decimal("50000"),
) -> EnrichedPosition:
    """Return an EQUITY enriched position (unsupported by FI engine)."""
    return EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=position_id,
        isin=isin,
        valuation_date="2026-06-10",
        quantity=Decimal("100"),
        market_value=market_value_base_ccy,
        position_currency="USD",
        asset_class="EQUITY",
        instrument_currency="USD",
        market_value_base_ccy=market_value_base_ccy,
        fund_base_currency="USD",
        weight=Decimal("0.5"),
    )


def make_portfolio(
    positions: list[EnrichedPosition],
    nav: Decimal = Decimal("100000"),
    fund_base_currency: str = "USD",
) -> RiskReadyPortfolio:
    """Return a RiskReadyPortfolio from the given positions."""
    return RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2026-06-10",
        fund_base_currency=fund_base_currency,
        nav=nav,
        positions=positions,
    )


class FakePricer:
    """Fake pricer that returns a predictable result for testing engine orchestration."""

    def __init__(self, rate_pnl: Decimal, credit_pnl: Decimal) -> None:
        self._rate_pnl = rate_pnl
        self._credit_pnl = credit_pnl
        self.calls: list[tuple[EnrichedPosition, FixedIncomeStressScenario]] = []

    def price_position(
        self,
        position: EnrichedPosition,
        scenario: FixedIncomeStressScenario,
    ) -> FixedIncomeStressPositionResult:
        self.calls.append((position, scenario))
        dirty_value = position.market_value_base_ccy
        total = self._rate_pnl + self._credit_pnl
        return FixedIncomeStressPositionResult(
            position_id=position.position_id,
            isin=position.isin,
            asset_class=position.asset_class,
            shock_type=scenario.shock_type,
            rate_shock_bps=scenario.rate_shock_bps,
            spread_shock_bps=scenario.spread_shock_bps,
            modified_duration=position.modified_duration,
            spread_duration=position.spread_duration,
            current_dirty_value_base_ccy=dirty_value,
            stressed_dirty_value_base_ccy=dirty_value + total,
            rate_pnl=self._rate_pnl,
            credit_pnl=self._credit_pnl,
            total_pnl=total,
        )


class TestFixedIncomeStressEngine:
    @staticmethod
    def make_engine(
        rate_pnl: Decimal = Decimal("-4000"),
        credit_pnl: Decimal = Decimal("0"),
    ) -> tuple[FixedIncomeStressEngine, FakePricer]:
        """Return engine wired to a FakePricer for orchestration tests."""
        pricer = FakePricer(rate_pnl=rate_pnl, credit_pnl=credit_pnl)
        engine = FixedIncomeStressEngine(pricer)
        return engine, pricer

    @staticmethod
    def make_real_engine() -> FixedIncomeStressEngine:
        """Return engine wired to DurationBasedFixedIncomePricer for arithmetic tests."""
        return FixedIncomeStressEngine(DurationBasedFixedIncomePricer())

    # --- Basic stress cases ---

    def test_single_bond_stressed(self) -> None:
        """Engine stresses a single BOND position and returns one result."""
        engine, _ = self.make_engine(rate_pnl=Decimal("-4000"), credit_pnl=Decimal("0"))
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("0"),
        )
        portfolio = make_portfolio([position], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        results = engine.stress(fi_input)

        assert len(results) == 1
        result = results[0]
        assert result.total_pnl == Decimal("-4000")
        assert result.num_bond_positions == 1
        assert result.num_cash_positions == 0

    def test_multiple_scenarios_return_one_result_each(self) -> None:
        """Engine returns one FixedIncomeStressPortfolioResult per scenario."""
        engine, _ = self.make_engine()
        position = make_bond_position()
        portfolio = make_portfolio([position])
        scenarios = [
            make_scenario(scenario_id="S1", rate_shock_bps=100, spread_shock_bps=0),
            make_scenario(scenario_id="S2", rate_shock_bps=200, spread_shock_bps=0),
        ]
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=scenarios)

        results = engine.stress(fi_input)
        assert len(results) == 2
        assert results[0].scenario_id == "S1"
        assert results[1].scenario_id == "S2"

    def test_bond_plus_cash_portfolio(self) -> None:
        """BOND is stressed; base-currency CASH is unchanged."""
        engine, _ = self.make_engine(rate_pnl=Decimal("-4000"), credit_pnl=Decimal("0"))
        bond = make_bond_position(
            position_id=1,
            market_value_base_ccy=Decimal("80000"),
            modified_duration=Decimal("4.0"),
            spread_duration=Decimal("0"),
        )
        cash = make_cash_position(position_id=2, market_value_base_ccy=Decimal("20000"))
        portfolio = make_portfolio([bond, cash], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        result = engine.stress(fi_input)[0]

        # Only bond P&L contributes; cash is zero
        assert result.num_bond_positions == 1
        assert result.num_cash_positions == 1
        cash_result = next(p for p in result.stressed_positions if p.asset_class == "CASH")
        assert cash_result.rate_pnl == Decimal("0")
        assert cash_result.credit_pnl == Decimal("0")
        assert cash_result.total_pnl == Decimal("0")
        assert cash_result.stressed_dirty_value_base_ccy == Decimal("20000")

    def test_all_cash_portfolio_zero_pnl(self) -> None:
        """All-cash portfolio produces zero total P&L and zero loss_pct_nav."""
        engine, _ = self.make_engine()
        cash = make_cash_position(market_value_base_ccy=Decimal("100000"))
        portfolio = make_portfolio([cash], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        result = engine.stress(fi_input)[0]

        assert result.total_pnl == Decimal("0")
        assert result.loss_pct_nav == Decimal("0")
        assert result.stressed_nav == Decimal("100000")
        assert result.num_bond_positions == 0
        assert result.num_cash_positions == 1

    # --- Asset class rejection ---

    def test_equity_position_raises_unsupported_asset_class(self) -> None:
        """EQUITY in portfolio raises UnsupportedAssetClassError."""
        engine, _ = self.make_engine()
        equity = make_equity_position()
        portfolio = make_portfolio([equity])
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        with pytest.raises(UnsupportedAssetClassError) as exc_info:
            engine.stress(fi_input)

        assert exc_info.value.asset_class == "EQUITY"

    def test_foreign_currency_cash_raises_unsupported(self) -> None:
        """Foreign-currency CASH raises UnsupportedAssetClassError."""
        engine, _ = self.make_engine()
        foreign_cash = make_cash_position(
            instrument_currency="EUR",  # fund base is USD
            fund_base_currency="USD",
        )
        portfolio = make_portfolio([foreign_cash], fund_base_currency="USD")
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        with pytest.raises(UnsupportedAssetClassError) as exc_info:
            engine.stress(fi_input)

        assert exc_info.value.asset_class == "CASH"

    # --- Aggregation correctness ---

    def test_total_rate_pnl_equals_sum_of_position_rate_pnls(self) -> None:
        """total_rate_pnl = sum of all position rate_pnl values."""
        engine, _ = self.make_engine(rate_pnl=Decimal("-2000"), credit_pnl=Decimal("0"))
        positions = [
            make_bond_position(position_id=1, market_value_base_ccy=Decimal("50000")),
            make_bond_position(position_id=2, market_value_base_ccy=Decimal("50000")),
        ]
        portfolio = make_portfolio(positions, nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        result = engine.stress(fi_input)[0]

        expected = sum(p.rate_pnl for p in result.stressed_positions)
        assert result.total_rate_pnl == expected

    def test_total_credit_pnl_equals_sum_of_position_credit_pnls(self) -> None:
        """total_credit_pnl = sum of all position credit_pnl values."""
        engine, _ = self.make_engine(rate_pnl=Decimal("0"), credit_pnl=Decimal("-1500"))
        positions = [
            make_bond_position(position_id=1, market_value_base_ccy=Decimal("50000")),
            make_bond_position(position_id=2, market_value_base_ccy=Decimal("50000")),
        ]
        portfolio = make_portfolio(positions, nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[
                make_scenario(shock_type="SPREAD_SHOCK", rate_shock_bps=0, spread_shock_bps=50)
            ],
        )

        result = engine.stress(fi_input)[0]

        expected = sum(p.credit_pnl for p in result.stressed_positions)
        assert result.total_credit_pnl == expected

    def test_total_pnl_equals_rate_plus_credit(self) -> None:
        """total_pnl = total_rate_pnl + total_credit_pnl."""
        engine, _ = self.make_engine(rate_pnl=Decimal("-3000"), credit_pnl=Decimal("-1000"))
        position = make_bond_position()
        portfolio = make_portfolio([position])
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[
                make_scenario(shock_type="COMBINED", rate_shock_bps=100, spread_shock_bps=50)
            ],
        )

        result = engine.stress(fi_input)[0]
        assert result.total_pnl == result.total_rate_pnl + result.total_credit_pnl

    def test_stressed_nav_equals_nav_plus_total_pnl(self) -> None:
        """stressed_nav = current_nav + total_pnl."""
        engine, _ = self.make_engine(rate_pnl=Decimal("-4000"), credit_pnl=Decimal("0"))
        position = make_bond_position()
        portfolio = make_portfolio([position], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        result = engine.stress(fi_input)[0]
        assert result.stressed_nav == result.current_nav + result.total_pnl

    # --- loss_pct_nav ---

    def test_loss_scenario_produces_positive_loss_pct_nav(self) -> None:
        """Loss scenario: loss_pct_nav is positive."""
        engine = self.make_real_engine()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("5.0"),
            spread_duration=Decimal("0"),
        )
        portfolio = make_portfolio([position], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[make_scenario(rate_shock_bps=100, spread_shock_bps=0)],
        )

        result = engine.stress(fi_input)[0]
        assert result.loss_pct_nav > Decimal("0")

    def test_gain_scenario_gives_zero_loss_pct_nav(self) -> None:
        """Gain scenario (yield down): loss_pct_nav is zero."""
        engine = self.make_real_engine()
        position = make_bond_position(
            market_value_base_ccy=Decimal("100000"),
            modified_duration=Decimal("5.0"),
            spread_duration=Decimal("0"),
        )
        portfolio = make_portfolio([position], nav=Decimal("100000"))
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[make_scenario(rate_shock_bps=-50, spread_shock_bps=0)],  # yield down = gain
        )

        result = engine.stress(fi_input)[0]
        assert result.loss_pct_nav == Decimal("0")

    # --- Scenario metadata ---

    def test_scenario_metadata_copied_to_portfolio_result(self) -> None:
        """Scenario fields are faithfully copied to FixedIncomeStressPortfolioResult."""
        engine, _ = self.make_engine()
        position = make_bond_position()
        portfolio = make_portfolio([position])
        scenario = make_scenario(
            scenario_id="FI_COMBINED_001",
            shock_type="COMBINED",
            rate_shock_bps=75,
            spread_shock_bps=30,
        )
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[scenario])

        result = engine.stress(fi_input)[0]

        assert result.scenario_id == "FI_COMBINED_001"
        assert result.shock_type == "COMBINED"
        assert result.rate_shock_bps == 75
        assert result.spread_shock_bps == 30

    # --- Delegation to pricer ---

    def test_engine_delegates_to_injected_pricer(self) -> None:
        """Engine calls pricer.price_position for each BOND position."""
        engine, fake_pricer = self.make_engine(
            rate_pnl=Decimal("-2000"), credit_pnl=Decimal("-500")
        )
        bond1 = make_bond_position(position_id=1)
        bond2 = make_bond_position(position_id=2)
        portfolio = make_portfolio([bond1, bond2])
        scenario = make_scenario()
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[scenario])

        engine.stress(fi_input)

        # Pricer was called once per bond position
        assert len(fake_pricer.calls) == 2
        called_ids = {pos.position_id for pos, _ in fake_pricer.calls}
        assert called_ids == {1, 2}

    def test_engine_does_not_call_pricer_for_cash(self) -> None:
        """Engine does not call pricer for CASH positions."""
        engine, fake_pricer = self.make_engine()
        bond = make_bond_position(position_id=1)
        cash = make_cash_position(position_id=2)
        portfolio = make_portfolio([bond, cash])
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        engine.stress(fi_input)

        # Pricer called only for the bond
        assert len(fake_pricer.calls) == 1
        assert fake_pricer.calls[0][0].position_id == 1

    # --- Missing duration propagation ---

    def test_missing_duration_error_propagated_from_pricer(self) -> None:
        """MissingDurationError from the pricer surfaces unchanged to the caller."""
        engine = self.make_real_engine()
        position = make_bond_position(
            modified_duration=None,  # will fail for rate shock
            spread_duration=Decimal("0"),
        )
        portfolio = make_portfolio([position])
        fi_input = FixedIncomeStressInput(
            portfolio=portfolio,
            scenarios=[make_scenario(rate_shock_bps=100, spread_shock_bps=0)],
        )

        with pytest.raises(MissingDurationError) as exc_info:
            engine.stress(fi_input)

        assert exc_info.value.field == "modified_duration"

    # --- Position counts ---

    def test_num_bond_and_cash_positions_correct(self) -> None:
        """num_bond_positions and num_cash_positions are counted correctly."""
        engine, _ = self.make_engine()
        positions = [
            make_bond_position(position_id=1),
            make_bond_position(position_id=2),
            make_cash_position(position_id=3),
        ]
        portfolio = make_portfolio(positions)
        fi_input = FixedIncomeStressInput(portfolio=portfolio, scenarios=[make_scenario()])

        result = engine.stress(fi_input)[0]

        assert result.num_bond_positions == 2
        assert result.num_cash_positions == 1
