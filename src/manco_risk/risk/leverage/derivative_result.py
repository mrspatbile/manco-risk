"""Result model for derivative leverage exposure calculation.

Pure data model for derivative exposure engine output.
"""

from pydantic import BaseModel, ConfigDict

from manco_risk.risk.leverage.derivative_models import DerivativeRecord
from manco_risk.risk.leverage.models import (
    LeverageExposureSourceContribution,
    UnsupportedLeverageExposure,
)


class DerivativeExposureResult(BaseModel):
    """Result of derivative leverage exposure calculation.

    Fields:
    - derivative_records: Input derivative records (for reference/audit).
    - source_contribution: Aggregated DERIVATIVE source-level exposure contribution.
      None if no usable derivative exposures exist.
    - unsupported_exposures: Derivatives without usable exposure data.
    - warnings: Processing warnings (e.g., exposure selection, data issues).
    """

    derivative_records: list[DerivativeRecord]
    source_contribution: LeverageExposureSourceContribution | None
    unsupported_exposures: list[UnsupportedLeverageExposure]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)
