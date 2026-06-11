"""Result model for SFT leverage exposure calculation.

Pure data model for SFT exposure engine output.
"""

from pydantic import BaseModel, ConfigDict

from manco_risk.risk.leverage.models import LeverageExposureSourceContribution
from manco_risk.risk.leverage.sft_models import SFTRecord


class SFTExposureResult(BaseModel):
    """Result of SFT leverage exposure calculation.

    Fields:
    - sft_records: Input SFT records (for reference/audit).
    - source_contributions: Source-level exposure contributions for SFT_REPO,
      SFT_REVERSE_REPO, and/or SECURITIES_LENDING sources.
    - warnings: Processing warnings (e.g., data quality issues).
    """

    sft_records: list[SFTRecord]
    source_contributions: list[LeverageExposureSourceContribution]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)
