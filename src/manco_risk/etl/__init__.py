"""ETL and data ingestion layer for manco-risk.

Provides:
- Position input schema and validation
- CSV loading and normalization
- Data validation at ingestion boundary
"""

from manco_risk.etl.position_loader import PositionInput, PositionLoader

__all__ = [
    "PositionInput",
    "PositionLoader",
]
