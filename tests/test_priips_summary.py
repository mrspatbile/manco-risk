"""Tests for PRIIPs Summary service.

Tests the PRIIPSSummaryService against consistency validation and realistic
PRIIPs output assemblies.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.priips import (
    PerformanceScenariosInput,
    PRIIPSCostsInput,
    PRIIPSSummaryService,
    SRIInput,
)


class TestPRIIPSSummaryServiceBasic:
    """Test basic summary assembly."""

    def test_valid_summary_assembly(self):
        """Service accepts valid result objects and returns summary."""
        sri_input = SRIInput(
            product_id="UCITS_BALANCED",
            valuation_date=date(2026, 7, 1),
            mrm_class=4,
            crm_class=2,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="UCITS_BALANCED",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("-0.25"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.03"),
            favourable_return=Decimal("0.15"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="UCITS_BALANCED",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0.0005"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        summary = PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

        assert summary.product_id == "UCITS_BALANCED"
        assert summary.valuation_date == date(2026, 7, 1)
        assert summary.methodology_version == "2017/653"
        assert summary.recommended_holding_period_years == 5

    def test_summary_contains_all_sections(self):
        """Summary includes all three result sections."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        summary = PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

        assert "SRI" in summary.included_sections
        assert "Performance Scenarios" in summary.included_sections
        assert "Costs" in summary.included_sections
        assert len(summary.included_sections) == 3

    def test_summary_references_original_results(self):
        """Summary contains references to original result objects."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=3,
            crm_class=2,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            stress_return=Decimal("-0.15"),
            unfavourable_return=Decimal("-0.05"),
            moderate_return=Decimal("0.05"),
            favourable_return=Decimal("0.20"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,
            entry_cost=Decimal("0.005"),
            exit_cost=Decimal("0.003"),
            ongoing_cost=Decimal("0.004"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0.0002"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        summary = PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

        assert summary.sri_result.sri_class == sri_result.sri_class
        assert summary.performance_scenarios_result.stress_return == scenarios_result.stress_return
        assert summary.costs_result.entry_cost == costs_result.entry_cost


class TestConsistencyValidation:
    """Test consistency validation between result objects."""

    def test_product_id_mismatch_rejected(self):
        """Mismatched product_id raises ValueError."""
        sri_input = SRIInput(
            product_id="PRODUCT_A",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="PRODUCT_B",  # Mismatch!
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="PRODUCT_A",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        with pytest.raises(ValueError, match="Product IDs are not consistent"):
            PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

    def test_valuation_date_mismatch_rejected(self):
        """Mismatched valuation_date raises ValueError."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 6, 30),  # Mismatch!
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        with pytest.raises(ValueError, match="Valuation dates are not consistent"):
            PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

    def test_methodology_version_mismatch_rejected(self):
        """Mismatched methodology_version raises ValueError."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2021/2268",  # Mismatch!
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        with pytest.raises(ValueError, match="Methodology versions are not consistent"):
            PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

    def test_holding_period_mismatch_rejected(self):
        """Mismatched recommended_holding_period_years raises ValueError."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=3,  # Mismatch!
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        with pytest.raises(ValueError, match="Recommended holding periods are not consistent"):
            PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)


class TestResultImmutability:
    """Test that PRIIPSSummaryResult is immutable."""

    def test_result_is_frozen(self):
        """PRIIPSSummaryResult cannot be mutated after creation."""
        sri_input = SRIInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            mrm_class=1,
            crm_class=1,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            stress_return=Decimal("0"),
            unfavourable_return=Decimal("0"),
            moderate_return=Decimal("0"),
            favourable_return=Decimal("0"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="TEST",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=1,
            entry_cost=Decimal("0"),
            exit_cost=Decimal("0"),
            ongoing_cost=Decimal("0"),
            transaction_cost=Decimal("0"),
            incidental_cost=Decimal("0"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        summary = PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            summary.product_id = "NEW_PRODUCT"


class TestRealisticExample:
    """Test realistic PRIIPs summary example."""

    def test_realistic_ucits_balanced_summary(self):
        """Realistic UCITS balanced fund summary assembly."""
        sri_input = SRIInput(
            product_id="UCITS_BALANCED_EUR",
            valuation_date=date(2026, 7, 1),
            mrm_class=4,
            crm_class=2,
        )
        from manco_risk.risk.priips import SRIEngine

        sri_result = SRIEngine.calculate(sri_input)

        scenarios_input = PerformanceScenariosInput(
            product_id="UCITS_BALANCED_EUR",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            stress_return=Decimal("-0.247"),
            unfavourable_return=Decimal("-0.052"),
            moderate_return=Decimal("0.033"),
            favourable_return=Decimal("0.162"),
        )
        from manco_risk.risk.priips import PerformanceScenariosEngine

        scenarios_result = PerformanceScenariosEngine.calculate(scenarios_input)

        costs_input = PRIIPSCostsInput(
            product_id="UCITS_BALANCED_EUR",
            valuation_date=date(2026, 7, 1),
            methodology_version="2017/653",
            recommended_holding_period_years=5,
            entry_cost=Decimal("0.01"),
            exit_cost=Decimal("0.005"),
            ongoing_cost=Decimal("0.005"),
            transaction_cost=Decimal("0.001"),
            incidental_cost=Decimal("0.0005"),
        )
        from manco_risk.risk.priips import PRIIPSCostsEngine

        costs_result = PRIIPSCostsEngine.calculate(costs_input)

        summary = PRIIPSSummaryService.build(sri_result, scenarios_result, costs_result)

        assert summary.product_id == "UCITS_BALANCED_EUR"
        assert summary.sri_result.sri_class == 4
        assert summary.performance_scenarios_result.moderate_return == Decimal("0.033")
        assert summary.costs_result.ongoing_cost == Decimal("0.005")
