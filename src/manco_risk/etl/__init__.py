"""ETL and data ingestion layer for manco-risk.

Provides:
- Position input schema and validation
- CSV loading and normalization
- Data validation at ingestion boundary
- Position input mapping and persistence
- Position validation framework
- Enriched position models for risk calculation
- Position enrichment engine
"""

from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.etl.enrichment_service import EnrichmentService
from manco_risk.etl.exceptions import (
    InstrumentReferenceNotFoundError,
    MissingFXRateError,
    NAVSnapshotNotFoundError,
    PositionEnrichmentError,
    PositionValidationFailure,
)
from manco_risk.etl.position_enricher import PositionEnricher
from manco_risk.etl.position_loader import PositionInput, PositionLoader
from manco_risk.etl.position_mapper import PositionMapper
from manco_risk.etl.position_validator import (
    PositionValidator,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)

__all__ = [
    "PositionInput",
    "PositionLoader",
    "PositionMapper",
    "PositionValidator",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "PositionValidationFailure",
    "EnrichedPosition",
    "RiskReadyPortfolio",
    "PositionEnricher",
    "PositionEnrichmentError",
    "InstrumentReferenceNotFoundError",
    "MissingFXRateError",
    "NAVSnapshotNotFoundError",
    "EnrichmentService",
]
