"""Result model for physical instrument leverage exposure calculation.

Pure data model for physical instrument exposure engine output.
"""

from pydantic import BaseModel, ConfigDict

from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    LeveragePositionContribution,
    UnsupportedLeverageExposure,
)


class PhysicalInstrumentExposureResult(BaseModel):
    """Result of physical instrument leverage exposure calculation.

    Fields:
    - position_contributions: Position-level exposure breakdown for physical instruments.
    - source_contribution: Aggregated source-level exposure (None if no physical instruments).
    - unsupported_exposures: Any unsupported asset classes encountered.
    - warnings: Processing warnings (e.g., data quality issues).
    """

    position_contributions: list[LeveragePositionContribution]
    source_contribution: LeverageExposureSourceContribution | None
    unsupported_exposures: list[UnsupportedLeverageExposure]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)
