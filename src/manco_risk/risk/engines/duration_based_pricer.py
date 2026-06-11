"""Duration-approximation pricer for fixed-income stress testing.

Phase 1 implementation of the FixedIncomeStressPricer protocol. Uses modified
duration for rate shocks and spread duration for credit spread shocks.

This is a first-order linear approximation. It does not reprice from cashflows,
does not use a discount curve, and does not compute convexity corrections.

A future QuantLibFixedIncomePricer will satisfy the same FixedIncomeStressPricer
protocol using full cashflow repricing.

Dirty value assumption (Phase 1):
    market_value_base_ccy from EnrichedPosition is used as the dirty market
    value. Fund administrator files report dirty values (full price × face +
    accrued interest). No accrued interest computation is performed here.

Formulas:
    rate_shock_decimal   = Decimal(rate_shock_bps) / Decimal("10000")
    spread_shock_decimal = Decimal(spread_shock_bps) / Decimal("10000")

    rate_pnl   = -modified_duration × rate_shock_decimal × dirty_value
    credit_pnl = -spread_duration   × spread_shock_decimal × dirty_value

    total_pnl            = rate_pnl + credit_pnl
    stressed_dirty_value = dirty_value + total_pnl

Zero-bps exemption:
    If rate_shock_bps == 0: rate_pnl = 0; modified_duration is not required.
    If spread_shock_bps == 0: credit_pnl = 0; spread_duration is not required.

Sign conventions:
    Positive rate_shock_bps (yield rises) → negative rate_pnl (loss).
    Negative rate_shock_bps (yield falls) → positive rate_pnl (gain).
    Positive spread_shock_bps (spread widens) → negative credit_pnl (loss).
"""

from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition
from manco_risk.risk.exceptions import MissingDurationError
from manco_risk.risk.models.fixed_income_stress_position_result import (
    FixedIncomeStressPositionResult,
)
from manco_risk.risk.models.fixed_income_stress_scenario import FixedIncomeStressScenario

_TEN_THOUSAND = Decimal("10000")


class DurationBasedFixedIncomePricer:
    """Duration-approximation pricer implementing FixedIncomeStressPricer.

    Stateless; no constructor arguments required.
    """

    def price_position(
        self,
        position: EnrichedPosition,
        scenario: FixedIncomeStressScenario,
    ) -> FixedIncomeStressPositionResult:
        """Compute stressed dirty value and decomposed P&L for one position.

        Parameters
        ----------
        position : EnrichedPosition
            Enriched position. market_value_base_ccy is treated as the dirty
            market value (Phase 1 assumption).
        scenario : FixedIncomeStressScenario
            Scenario specifying rate_shock_bps and spread_shock_bps.

        Returns
        -------
        FixedIncomeStressPositionResult
            Decomposed P&L (rate_pnl, credit_pnl, total_pnl) and
            stressed_dirty_value_base_ccy.

        Raises
        ------
        MissingDurationError
            If rate_shock_bps != 0 and position.modified_duration is None.
            If spread_shock_bps != 0 and position.spread_duration is None.
        """
        dirty_value = position.market_value_base_ccy
        rate_shock_bps = scenario.rate_shock_bps
        spread_shock_bps = scenario.spread_shock_bps

        rate_pnl = self._compute_rate_pnl(position, rate_shock_bps, dirty_value)
        credit_pnl = self._compute_credit_pnl(position, spread_shock_bps, dirty_value)

        total_pnl = rate_pnl + credit_pnl
        stressed_dirty_value = dirty_value + total_pnl

        return FixedIncomeStressPositionResult(
            position_id=position.position_id,
            isin=position.isin,
            position_name=None,
            asset_class=position.asset_class,
            shock_type=scenario.shock_type,
            rate_shock_bps=rate_shock_bps,
            spread_shock_bps=spread_shock_bps,
            modified_duration=position.modified_duration,
            spread_duration=position.spread_duration,
            current_dirty_value_base_ccy=dirty_value,
            stressed_dirty_value_base_ccy=stressed_dirty_value,
            rate_pnl=rate_pnl,
            credit_pnl=credit_pnl,
            total_pnl=total_pnl,
        )

    def _compute_rate_pnl(
        self,
        position: EnrichedPosition,
        rate_shock_bps: int,
        dirty_value: Decimal,
    ) -> Decimal:
        if rate_shock_bps == 0:
            return Decimal("0")
        if position.modified_duration is None:
            raise MissingDurationError(
                isin=position.isin,
                field="modified_duration",
                reason=f"required for non-zero rate_shock_bps={rate_shock_bps}",
            )
        rate_shock_decimal = Decimal(rate_shock_bps) / _TEN_THOUSAND
        return -position.modified_duration * rate_shock_decimal * dirty_value

    def _compute_credit_pnl(
        self,
        position: EnrichedPosition,
        spread_shock_bps: int,
        dirty_value: Decimal,
    ) -> Decimal:
        if spread_shock_bps == 0:
            return Decimal("0")
        if position.spread_duration is None:
            raise MissingDurationError(
                isin=position.isin,
                field="spread_duration",
                reason=f"required for non-zero spread_shock_bps={spread_shock_bps}",
            )
        spread_shock_decimal = Decimal(spread_shock_bps) / _TEN_THOUSAND
        return -position.spread_duration * spread_shock_decimal * dirty_value
