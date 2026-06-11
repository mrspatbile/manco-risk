"""Result model for direct borrowing leverage exposure calculation.

Pure data model for direct borrowing exposure engine output.
"""

from pydantic import BaseModel, ConfigDict

from manco_risk.risk.leverage.borrowing_models import BorrowingRecord
from manco_risk.risk.leverage.models import LeverageExposureSourceContribution


class DirectBorrowingExposureResult(BaseModel):
    """Result of direct borrowing leverage exposure calculation.

    Fields:
    - borrowing_records: Input borrowing records (for reference/audit).
    - source_contributions: Source-level exposure contributions for DIRECT_BORROWING
      and/or REINVESTED_BORROWING.
    - warnings: Processing warnings (e.g., data quality issues).
    """

    borrowing_records: list[BorrowingRecord]
    source_contributions: list[LeverageExposureSourceContribution]
    warnings: list[str]

    model_config = ConfigDict(frozen=True)
