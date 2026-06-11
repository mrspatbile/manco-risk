"""Reverse equity stress engine.

Calculates the parallel equity shock required to reach a target NAV loss.
Uses EquityStressEngine to apply the calculated shock.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.engines.equity_stress import EquityStressEngine
from manco_risk.risk.models.reverse_stress_input import ReverseStressInput
from manco_risk.risk.models.reverse_stress_result import ReverseStressResult
from manco_risk.risk.models.stress_scenario import StressScenario
from manco_risk.risk.models.stress_test_input import StressTestInput


class ReverseEquityStressEngine:
    """Pure reverse stress engine for equity-like portfolios.

    Calculates the parallel equity shock required to reach a target NAV loss percentage.

    Given a portfolio and a target loss percentage:
    1. Validates asset classes (same as forward stress)
    2. Calculates equity-like market value (sum of supported non-cash positions)
    3. Calculates target loss amount and required shock
    4. Checks feasibility:
       - Zero equity-like exposure → infeasible (required_shock=None)
       - Required shock < -1.0 → infeasible (required_shock kept for diagnostics)
       - Target loss >= NAV → infeasible (target loss too large)
       - Otherwise → feasible
    5. If feasible:
       - Creates synthetic StressScenario with calculated shock
       - Applies shock using EquityStressEngine
       - Returns result with populated stress_result
    6. If infeasible:
       - Returns result with is_feasible=False
       - stress_result=None
       - Explains infeasibility reason

    Special cases:
    - target_loss_pct = 0 → feasible, required_shock = 0
    - All-cash portfolio → infeasible, required_shock = None
    - Shock < -100% → infeasible, required_shock retained for diagnostics
    """

    def __init__(self):
        """Initialize reverse stress engine."""
        self.stress_engine = EquityStressEngine()

    def calculate(self, input: ReverseStressInput) -> ReverseStressResult:
        """Calculate reverse stress to reach target NAV loss.

        Parameters
        ----------
        input : ReverseStressInput
            Portfolio and target NAV loss percentage.

        Returns
        -------
        ReverseStressResult
            Calculated shock, feasibility status, and underlying stress result if feasible.

        Raises
        ------
        UnsupportedAssetClassError
            If any position has an unsupported asset class or if cash is
            in a foreign currency.
        """
        portfolio = input.portfolio
        target_loss_pct = input.target_loss_pct
        current_nav = portfolio.nav
        current_valuation_date = portfolio.valuation_date

        # Validate portfolio asset classes (reuse forward stress validation)
        self.stress_engine._validate_portfolio_asset_classes(portfolio)

        # Calculate equity-like market value (sum of non-cash, supported positions)
        equity_like_market_value = Decimal("0")
        for position in portfolio.positions:
            if position.asset_class != "CASH":
                equity_like_market_value += position.market_value_base_ccy

        # Calculate target loss amount
        target_loss_amount = current_nav * target_loss_pct

        # Check for infeasibility: zero equity-like exposure
        if equity_like_market_value == Decimal("0"):
            return ReverseStressResult(
                fund_id=portfolio.fund_id,
                valuation_date=date.fromisoformat(current_valuation_date),
                scenario_id=input.scenario_id,
                scenario_name=input.scenario_name,
                scenario_type=input.scenario_type,
                scenario_source=input.scenario_source,
                target_loss_pct=target_loss_pct,
                target_loss_amount=target_loss_amount,
                equity_like_market_value=equity_like_market_value,
                required_shock=None,
                is_feasible=False,
                infeasibility_reason="No equity-like exposure available to shock",
                stress_result=None,
            )

        # Calculate required shock
        required_shock = -target_loss_amount / equity_like_market_value

        # Check for infeasibility: shock < -100% (below -1.0)
        if required_shock < Decimal("-1.0"):
            return ReverseStressResult(
                fund_id=portfolio.fund_id,
                valuation_date=date.fromisoformat(current_valuation_date),
                scenario_id=input.scenario_id,
                scenario_name=input.scenario_name,
                scenario_type=input.scenario_type,
                scenario_source=input.scenario_source,
                target_loss_pct=target_loss_pct,
                target_loss_amount=target_loss_amount,
                equity_like_market_value=equity_like_market_value,
                required_shock=required_shock,
                is_feasible=False,
                infeasibility_reason=f"Required shock {required_shock} exceeds -100%; "
                f"equity-like exposure ({equity_like_market_value}) insufficient to reach target loss "
                f"({target_loss_amount})",
                stress_result=None,
            )

        # Check for infeasibility: target loss >= NAV
        if target_loss_amount >= current_nav:
            return ReverseStressResult(
                fund_id=portfolio.fund_id,
                valuation_date=date.fromisoformat(current_valuation_date),
                scenario_id=input.scenario_id,
                scenario_name=input.scenario_name,
                scenario_type=input.scenario_type,
                scenario_source=input.scenario_source,
                target_loss_pct=target_loss_pct,
                target_loss_amount=target_loss_amount,
                equity_like_market_value=equity_like_market_value,
                required_shock=required_shock,
                is_feasible=False,
                infeasibility_reason=f"Target loss ({target_loss_amount}) >= NAV ({current_nav}); "
                f"would wipe out entire fund",
                stress_result=None,
            )

        # Feasible: create synthetic scenario and apply stress
        synthetic_scenario = StressScenario(
            scenario_id=input.scenario_id,
            scenario_name=input.scenario_name,
            scenario_type=input.scenario_type,
            scenario_source=input.scenario_source,
            shock_type="PARALLEL_EQUITY_REVERSE",
            shock_rate=required_shock,
            description=input.description,
        )

        stress_input = StressTestInput(portfolio=portfolio, scenarios=[synthetic_scenario])
        stress_results = self.stress_engine.stress(stress_input)
        stress_result = stress_results[0]

        return ReverseStressResult(
            fund_id=portfolio.fund_id,
            valuation_date=date.fromisoformat(current_valuation_date),
            scenario_id=input.scenario_id,
            scenario_name=input.scenario_name,
            scenario_type=input.scenario_type,
            scenario_source=input.scenario_source,
            target_loss_pct=target_loss_pct,
            target_loss_amount=target_loss_amount,
            equity_like_market_value=equity_like_market_value,
            required_shock=required_shock,
            is_feasible=True,
            infeasibility_reason=None,
            stress_result=stress_result,
        )
