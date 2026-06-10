"""End-to-end integration test: prices → returns → scenario P&Ls → VaR.

Tests the complete flow with hand-calculated deterministic values.
No randomness, no approximations.
"""

from datetime import date
from decimal import Decimal

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.engines.equity_scenarios import EquityScenarioPnLGenerator
from manco_risk.risk.engines.price_converter import PriceToReturnConverter
from manco_risk.risk.engines.var import HistoricalVaR
from manco_risk.risk.models.equity_scenario_pnl import EquityScenarioPnLInput
from manco_risk.risk.models.price_return import PricePoint, PriceToReturnInput
from manco_risk.risk.models.var_input import HistoricalVaRInput


def test_end_to_end_prices_to_var():
    """End-to-end: prices → returns → scenario P&Ls → VaR.

    Deterministic hand-calculated test with exact expected values.

    Portfolio:
    - NAV: 100,000 EUR
    - Position 1: 60,000 EUR (60% of NAV), ISIN "US0378331005"
    - Position 2: 40,000 EUR (40% of NAV), ISIN "IE00B4L5Y983"

    Data:
    - 6 price observations per ISIN → 5 daily returns per ISIN
    - Returns for ISIN 1: [-0.10, -0.05, 0.00, 0.02, 0.04]
    - Returns for ISIN 2: [-0.05, 0.00, 0.01, 0.02, 0.03]

    Expected scenario P&Ls (portfolio = 60% × ISIN1 + 40% × ISIN2):
    - Scenario 1: 60000 * -0.10 + 40000 * -0.05 = -8000
    - Scenario 2: 60000 * -0.05 + 40000 * 0.00 = -3000
    - Scenario 3: 60000 * 0.00 + 40000 * 0.01 = 400
    - Scenario 4: 60000 * 0.02 + 40000 * 0.02 = 2000
    - Scenario 5: 60000 * 0.04 + 40000 * 0.03 = 3600

    VaR at 80% confidence:
    - Sorted P&Ls: [-8000, -3000, 400, 2000, 3600]
    - Quantile index: floor(5 * (1 - 0.80)) = 1
    - Selected P&L: -3000
    - VaR value: 3000 EUR
    - VaR % NAV: 3000 / 100000 = 0.03
    """

    # === Step 1: Build prices from known returns ===
    # For ISIN 1, start at 100, apply returns: [-0.10, -0.05, 0.00, 0.02, 0.04]
    prices_isin1 = [Decimal("100")]
    for return_val in [
        Decimal("-0.10"),
        Decimal("-0.05"),
        Decimal("0.00"),
        Decimal("0.02"),
        Decimal("0.04"),
    ]:
        new_price = prices_isin1[-1] * (Decimal("1") + return_val)
        prices_isin1.append(new_price)

    # For ISIN 2, start at 100, apply returns: [-0.05, 0.00, 0.01, 0.02, 0.03]
    prices_isin2 = [Decimal("100")]
    for return_val in [
        Decimal("-0.05"),
        Decimal("0.00"),
        Decimal("0.01"),
        Decimal("0.02"),
        Decimal("0.03"),
    ]:
        new_price = prices_isin2[-1] * (Decimal("1") + return_val)
        prices_isin2.append(new_price)

    # Create price points with sequential dates
    price_points = []
    for i in range(6):
        scenario_date = date(2024, 1, 1 + i)
        price_points.append(
            PricePoint(isin="US0378331005", price_date=scenario_date, price=prices_isin1[i])
        )
        price_points.append(
            PricePoint(isin="IE00B4L5Y983", price_date=scenario_date, price=prices_isin2[i])
        )

    # === Step 3: Convert prices to returns ===
    converter = PriceToReturnConverter()
    price_input = PriceToReturnInput(price_points=price_points)
    price_result = converter.convert(price_input)

    # Verify converter output
    assert price_result.num_isins == 2
    assert price_result.num_price_points == 12
    assert price_result.num_returns == 10  # 5 per ISIN
    assert price_result.num_unique_return_dates == 5

    # Verify exact returns for ISIN 1
    for i, expected_return in enumerate(
        [Decimal("-0.10"), Decimal("-0.05"), Decimal("0.00"), Decimal("0.02"), Decimal("0.04")]
    ):
        scenario_date = date(2024, 1, 2 + i)
        actual_return = price_result.historical_returns["US0378331005"][scenario_date]
        # Allow tiny rounding due to Decimal division
        assert abs(actual_return - expected_return) < Decimal("0.0001")

    # Verify exact returns for ISIN 2
    for i, expected_return in enumerate(
        [Decimal("-0.05"), Decimal("0.00"), Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
    ):
        scenario_date = date(2024, 1, 2 + i)
        actual_return = price_result.historical_returns["IE00B4L5Y983"][scenario_date]
        assert abs(actual_return - expected_return) < Decimal("0.0001")

    # === Step 2a: Create portfolio and generate scenario P&Ls ===
    position1 = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=1,
        isin="US0378331005",
        valuation_date="2024-01-01",
        quantity=Decimal("400"),
        market_value=Decimal("60000.00"),
        position_currency="EUR",
        asset_class="EQUITY",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("60000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.6"),
    )

    position2 = EnrichedPosition(
        fund_id=1,
        position_snapshot_id=1,
        position_id=2,
        isin="IE00B4L5Y983",
        valuation_date="2024-01-01",
        quantity=Decimal("400"),
        market_value=Decimal("40000.00"),
        position_currency="EUR",
        asset_class="ETF",
        instrument_currency="EUR",
        market_value_base_ccy=Decimal("40000.00"),
        fund_base_currency="EUR",
        weight=Decimal("0.4"),
    )

    portfolio = RiskReadyPortfolio(
        fund_id=1,
        valuation_date="2024-01-01",
        fund_base_currency="EUR",
        nav=Decimal("100000.00"),
        positions=[position1, position2],
    )

    scenario_generator = EquityScenarioPnLGenerator()
    scenario_input = EquityScenarioPnLInput(
        portfolio=portfolio,
        historical_returns=price_result.historical_returns,
    )
    scenario_result = scenario_generator.generate(scenario_input)

    # Verify scenario P&Ls match expected values
    expected_pnls = [
        Decimal("-8000"),
        Decimal("-3000"),
        Decimal("400"),
        Decimal("2000"),
        Decimal("3600"),
    ]

    assert scenario_result.num_scenarios == 5
    assert scenario_result.num_equity_like_positions == 2
    assert scenario_result.num_cash_positions == 0

    for i, scenario_pnl in enumerate(scenario_result.scenario_pnls):
        expected_pnl = expected_pnls[i]
        actual_pnl = scenario_pnl.total_pnl
        # Portfolio P&L should match expected
        assert actual_pnl == expected_pnl, (
            f"Scenario {i + 1}: expected {expected_pnl}, got {actual_pnl}"
        )

    # === Step 1: Calculate VaR ===
    var_engine = HistoricalVaR()
    var_input = HistoricalVaRInput(
        portfolio=portfolio,
        confidence_level=Decimal("0.80"),
        horizon_days=1,
        scenario_pnls=scenario_result.scenario_pnls,
    )
    var_result = var_engine.calculate(var_input)

    # Verify VaR result
    assert var_result.fund_id == 1
    assert var_result.valuation_date == date(2024, 1, 1)
    assert var_result.confidence_level == Decimal("0.80")
    assert var_result.horizon_days == 1
    assert var_result.num_scenarios == 5
    assert var_result.quantile_index == 1

    # Expected: sorted P&Ls = [-8000, -3000, 400, 2000, 3600]
    # Quantile index 1 → selected P&L = -3000
    # VaR value = abs(-3000) = 3000
    # VaR % NAV = 3000 / 100000 = 0.03
    assert var_result.var_value == Decimal("3000")
    assert var_result.var_pct_nav == Decimal("3000") / Decimal("100000")
    assert var_result.var_pct_nav == Decimal("0.03")
