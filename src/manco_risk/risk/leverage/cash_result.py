"""Result model for cash and cash-equivalent leverage exposure calculation.

Pure data model for cash exposure engine output.
"""

from pydantic import BaseModel, ConfigDict

from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeveragePositionContribution,
    UnsupportedLeverageExposure,
)


class CashExposureResult(BaseModel):
    """Result of cash and cash-equivalent leverage exposure calculation.

    Fields:
    - position_contributions: Position-level records for cash positions.
      Note: These positions have zero gross and commitment exposure (excluded from leverage).
    - source_contribution: Aggregated source-level exposure (None if no cash positions).
      Will have zero gross and commitment exposure if present.
    - unsupported_exposures: Foreign-currency cash or other unhandled cases.
    - warnings: Processing warnings (e.g., foreign-currency cash detected).
    """

    position_contributions: list[LeveragePositionContribution]
    source_contribution: LeverageExposureSourceContribution | None
    unsupported_exposures: list[UnsupportedLeverageExposure]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)
