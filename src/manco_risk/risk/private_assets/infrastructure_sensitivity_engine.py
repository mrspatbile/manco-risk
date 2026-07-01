"""Infrastructure sensitivity analytics calculation engine.

Stateless orchestration of infrastructure sensitivity metrics packaging.

This engine validates and packages already-computed duration and inflation/interest-rate
sensitivity measures. No mathematical modeling, derivation, or forecasting performed.

Duration and sensitivity are supplied from external analysis sources.
"""

from manco_risk.risk.private_assets.infrastructure_sensitivity import (
    InfrastructureSensitivityInput,
    InfrastructureSensitivityResult,
)

__all__ = ["InfrastructureSensitivityEngine"]


class InfrastructureSensitivityEngine:
    """Stateless engine for infrastructure asset sensitivity analytics.

    Validates and packages duration and inflation/interest-rate sensitivity measures.
    No derivation or estimation performed.
    """

    @staticmethod
    def analyze(
        asset: InfrastructureSensitivityInput,
    ) -> InfrastructureSensitivityResult:
        """Analyze infrastructure asset sensitivity metrics.

        Parameters
        ----------
        asset : InfrastructureSensitivityInput
            Infrastructure asset with duration and sensitivity measures
            (already-computed from external analysis).

        Returns
        -------
        InfrastructureSensitivityResult
            Immutable result with duration and sensitivity metrics.

        Raises
        ------
        ValueError
            If input data is invalid.

        Notes
        -----
        No calculations performed. Input data is validated and packaged into
        an immutable result object.
        """
        return InfrastructureSensitivityResult(
            asset_id=asset.asset_id,
            valuation_date=asset.valuation_date,
            duration_years=asset.duration_years,
            inflation_sensitivity=asset.inflation_sensitivity,
            interest_rate_sensitivity=asset.interest_rate_sensitivity,
            methodology_version=asset.methodology_version,
        )
