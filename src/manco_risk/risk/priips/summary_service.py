"""PRIIPs Summary service.

Orchestration layer that assembles PRIIPs results into a summary.
"""

from manco_risk.risk.priips.costs import PRIIPSCostsResult
from manco_risk.risk.priips.performance_scenarios import PerformanceScenariosResult
from manco_risk.risk.priips.sri import SRIResult
from manco_risk.risk.priips.summary import PRIIPSSummaryResult


class PRIIPSSummaryService:
    """PRIIPs Summary orchestration service.

    Assembles individual PRIIPs result objects (SRI, scenarios, costs)
    into a consolidated summary.

    The service:
    1. Receives result objects from all PRIIPs engines.
    2. Validates consistency (product_id, valuation_date, methodology_version, RHP).
    3. Builds an immutable summary result.

    The service performs NO calculations, only validation and assembly.

    Reference:
    - Commission Delegated Regulation (EU) 2017/653, Annex II/IV/V/VI/VII:
      PRIIPs output requirements and KID content.
    """

    @staticmethod
    def build(
        sri_result: SRIResult,
        performance_scenarios_result: PerformanceScenariosResult,
        costs_result: PRIIPSCostsResult,
    ) -> PRIIPSSummaryResult:
        """Build consolidated PRIIPs summary from result objects.

        Parameters
        ----------
        sri_result : SRIResult
            Summary Risk Indicator result.
        performance_scenarios_result : PerformanceScenariosResult
            Performance Scenarios result.
        costs_result : PRIIPSCostsResult
            Costs result.

        Returns
        -------
        PRIIPSSummaryResult
            Consolidated PRIIPs summary.

        Raises
        ------
        ValueError
            If product_id, valuation_date, methodology_version, or
            recommended_holding_period_years are not consistent across
            all result objects.
        """
        # Validate product_id consistency
        product_ids = {
            sri_result.product_id,
            performance_scenarios_result.product_id,
            costs_result.product_id,
        }

        if len(product_ids) > 1:
            raise ValueError(f"Product IDs are not consistent: {product_ids}")

        product_id = sri_result.product_id

        # Validate valuation_date consistency
        valuation_dates = {
            sri_result.valuation_date,
            performance_scenarios_result.valuation_date,
            costs_result.valuation_date,
        }

        if len(valuation_dates) > 1:
            raise ValueError(f"Valuation dates are not consistent: {valuation_dates}")

        valuation_date = sri_result.valuation_date

        # Validate methodology_version consistency
        methodology_versions = {
            performance_scenarios_result.methodology_version,
            costs_result.methodology_version,
        }

        if len(methodology_versions) > 1:
            raise ValueError(f"Methodology versions are not consistent: {methodology_versions}")

        methodology_version = performance_scenarios_result.methodology_version

        # Validate recommended_holding_period_years consistency
        holding_periods = {
            performance_scenarios_result.recommended_holding_period_years,
            costs_result.recommended_holding_period_years,
        }

        if len(holding_periods) > 1:
            raise ValueError(f"Recommended holding periods are not consistent: {holding_periods}")

        recommended_holding_period_years = (
            performance_scenarios_result.recommended_holding_period_years
        )

        # List included sections
        included_sections = ["SRI", "Performance Scenarios", "Costs"]

        return PRIIPSSummaryResult(
            product_id=product_id,
            valuation_date=valuation_date,
            methodology_version=methodology_version,
            recommended_holding_period_years=recommended_holding_period_years,
            sri_result=sri_result,
            performance_scenarios_result=performance_scenarios_result,
            costs_result=costs_result,
            included_sections=included_sections,
        )
