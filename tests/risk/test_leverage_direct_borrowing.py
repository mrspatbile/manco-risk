"""Tests for direct borrowing leverage exposure engine.

Validates borrowing record models and exposure calculation for direct borrowing
and reinvested borrowing sources.
"""

from decimal import Decimal

import pytest

from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
)
from manco_risk.risk.leverage.borrowing_models import (
    BorrowingPurpose,
    BorrowingRecord,
    BorrowingTreatment,
)
from manco_risk.risk.leverage.direct_borrowing_engine import DirectBorrowingExposureEngine


class TestBorrowingPurposeEnum:
    """Test BorrowingPurpose enum."""

    def test_borrowing_purpose_values_exist(self):
        """All required borrowing purposes are defined."""
        assert BorrowingPurpose.LIQUIDITY_MANAGEMENT.value == "LIQUIDITY_MANAGEMENT"
        assert BorrowingPurpose.INVESTMENT_LEVERAGE.value == "INVESTMENT_LEVERAGE"
        assert BorrowingPurpose.SETTLEMENT.value == "SETTLEMENT"
        assert BorrowingPurpose.REDEMPTION_FINANCING.value == "REDEMPTION_FINANCING"
        assert BorrowingPurpose.OTHER.value == "OTHER"

    def test_borrowing_purpose_count(self):
        """All expected borrowing purposes are present."""
        assert len(list(BorrowingPurpose)) == 5


class TestBorrowingTreatmentEnum:
    """Test BorrowingTreatment enum."""

    def test_borrowing_treatment_values_exist(self):
        """All required borrowing treatments are defined."""
        assert BorrowingTreatment.UNREINVESTED.value == "UNREINVESTED"
        assert BorrowingTreatment.REINVESTED.value == "REINVESTED"
        assert BorrowingTreatment.PARTIALLY_REINVESTED.value == "PARTIALLY_REINVESTED"

    def test_borrowing_treatment_count(self):
        """All expected borrowing treatments are present."""
        assert len(list(BorrowingTreatment)) == 3


class TestBorrowingRecord:
    """Test BorrowingRecord model."""

    def test_valid_unreinvested_borrowing(self):
        """Valid unreinvested borrowing record."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )
        assert record.borrowing_id == "BORROW-001"
        assert record.amount_base_ccy == Decimal("1000000")
        assert record.reinvested_amount_base_ccy == Decimal("0")

    def test_valid_reinvested_borrowing(self):
        """Valid fully reinvested borrowing record."""
        record = BorrowingRecord(
            borrowing_id="BORROW-002",
            currency="EUR",
            amount_base_ccy=Decimal("2000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("2000000"),
        )
        assert record.treatment == BorrowingTreatment.REINVESTED
        assert record.reinvested_amount_base_ccy == record.amount_base_ccy

    def test_valid_partially_reinvested_borrowing(self):
        """Valid partially reinvested borrowing record."""
        record = BorrowingRecord(
            borrowing_id="BORROW-003",
            currency="EUR",
            amount_base_ccy=Decimal("5000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("3000000"),
        )
        assert record.treatment == BorrowingTreatment.PARTIALLY_REINVESTED
        unreinvested = record.amount_base_ccy - record.reinvested_amount_base_ccy
        assert unreinvested == Decimal("2000000")

    def test_rejects_empty_borrowing_id(self):
        """Borrowing ID cannot be empty."""
        with pytest.raises(ValueError, match="borrowing_id must be non-empty"):
            BorrowingRecord(
                borrowing_id="",
                currency="EUR",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.UNREINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("0"),
            )

    def test_rejects_empty_currency(self):
        """Currency cannot be empty."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.UNREINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("0"),
            )

    def test_rejects_negative_amount(self):
        """Amount cannot be negative."""
        with pytest.raises(ValueError, match="amount_base_ccy must be non-negative"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("-1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.UNREINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("0"),
            )

    def test_rejects_negative_reinvested_amount(self):
        """Reinvested amount cannot be negative."""
        with pytest.raises(ValueError, match="reinvested_amount_base_ccy must be non-negative"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.UNREINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("-500000"),
            )

    def test_rejects_reinvested_greater_than_amount(self):
        """Reinvested amount cannot exceed total amount."""
        with pytest.raises(ValueError, match="cannot exceed amount_base_ccy"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("1500000"),
            )

    def test_unreinvested_requires_zero_reinvested(self):
        """UNREINVESTED treatment requires zero reinvested amount."""
        with pytest.raises(ValueError, match="UNREINVESTED treatment requires"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
                treatment=BorrowingTreatment.UNREINVESTED,
                is_temporary=True,
                is_secured=False,
                reinvested_amount_base_ccy=Decimal("500000"),
            )

    def test_reinvested_requires_full_amount(self):
        """REINVESTED treatment requires full amount reinvested."""
        with pytest.raises(ValueError, match="REINVESTED treatment requires"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("2000000"),
                purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
                treatment=BorrowingTreatment.REINVESTED,
                is_temporary=False,
                is_secured=True,
                reinvested_amount_base_ccy=Decimal("1500000"),
            )

    def test_partially_reinvested_requires_valid_range(self):
        """PARTIALLY_REINVESTED requires amount between 0 and full."""
        with pytest.raises(ValueError, match="PARTIALLY_REINVESTED treatment requires"):
            BorrowingRecord(
                borrowing_id="BORROW-001",
                currency="EUR",
                amount_base_ccy=Decimal("5000000"),
                purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
                treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
                is_temporary=False,
                is_secured=True,
                reinvested_amount_base_ccy=Decimal("0"),
            )

    def test_model_is_frozen(self):
        """Model is immutable."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )
        with pytest.raises(Exception):  # Pydantic raises on frozen model
            record.borrowing_id = "BORROW-002"


class TestDirectBorrowingExposureEngine:
    """Test direct borrowing exposure calculation."""

    @pytest.fixture
    def engine(self):
        """Direct borrowing exposure engine."""
        return DirectBorrowingExposureEngine()

    def test_empty_borrowing_records(self, engine):
        """Empty borrowing records return empty source contributions."""
        result = engine.calculate([])

        assert len(result.borrowing_records) == 0
        assert len(result.source_contributions) == 0
        assert len(result.warnings) == 0

    def test_unreinvested_borrowing_creates_direct_borrowing_source(self, engine):
        """Unreinvested borrowing creates DIRECT_BORROWING source contribution."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 1
        src = result.source_contributions[0]
        assert src.source == LeverageSource.DIRECT_BORROWING
        assert src.gross_exposure == Decimal("1000000")
        assert src.commitment_exposure is None
        assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_reinvested_borrowing_creates_reinvested_source(self, engine):
        """Reinvested borrowing creates REINVESTED_BORROWING source contribution."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("2000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("2000000"),
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 1
        src = result.source_contributions[0]
        assert src.source == LeverageSource.REINVESTED_BORROWING
        assert src.gross_exposure == Decimal("2000000")
        assert src.commitment_exposure is None
        assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_partially_reinvested_creates_both_sources(self, engine):
        """Partially reinvested borrowing creates both source contributions."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("5000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("3000000"),
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 2
        sources = {src.source for src in result.source_contributions}
        assert LeverageSource.DIRECT_BORROWING in sources
        assert LeverageSource.REINVESTED_BORROWING in sources

        direct_src = next(
            s for s in result.source_contributions if s.source == LeverageSource.DIRECT_BORROWING
        )
        reinvested_src = next(
            s
            for s in result.source_contributions
            if s.source == LeverageSource.REINVESTED_BORROWING
        )

        assert direct_src.gross_exposure == Decimal("2000000")
        assert reinvested_src.gross_exposure == Decimal("3000000")

    def test_multiple_records_aggregate_by_source(self, engine):
        """Multiple records aggregate exposures by source."""
        record1 = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )
        record2 = BorrowingRecord(
            borrowing_id="BORROW-002",
            currency="EUR",
            amount_base_ccy=Decimal("2000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("2000000"),
        )
        record3 = BorrowingRecord(
            borrowing_id="BORROW-003",
            currency="EUR",
            amount_base_ccy=Decimal("3000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("1500000"),
        )

        result = engine.calculate([record1, record2, record3])

        sources = {src.source: src for src in result.source_contributions}
        assert len(sources) == 2

        direct_src = sources[LeverageSource.DIRECT_BORROWING]
        reinvested_src = sources[LeverageSource.REINVESTED_BORROWING]

        assert direct_src.gross_exposure == Decimal("1000000") + Decimal("1500000")
        assert reinvested_src.gross_exposure == Decimal("2000000") + Decimal("1500000")

    def test_commitment_exposure_none(self, engine):
        """Commitment exposure is None at source layer."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )

        result = engine.calculate([record])

        assert result.source_contributions[0].commitment_exposure is None

    def test_treatment_pending_method_rule(self, engine):
        """Treatment is PENDING_METHOD_RULE."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )

        result = engine.calculate([record])

        assert result.source_contributions[0].treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_no_warnings_on_valid_records(self, engine):
        """Valid borrowing records produce no warnings."""
        record = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )

        result = engine.calculate([record])

        assert len(result.warnings) == 0

    def test_result_model_is_frozen(self, engine):
        """Result model is immutable."""
        result = engine.calculate([])

        with pytest.raises(Exception):  # Pydantic raises on frozen model
            result.source_contributions = []

    def test_source_contributions_excluded_treatment(self, engine):
        """Source contributions are properly classified."""
        record1 = BorrowingRecord(
            borrowing_id="BORROW-001",
            currency="EUR",
            amount_base_ccy=Decimal("1000000"),
            purpose=BorrowingPurpose.LIQUIDITY_MANAGEMENT,
            treatment=BorrowingTreatment.UNREINVESTED,
            is_temporary=True,
            is_secured=False,
            reinvested_amount_base_ccy=Decimal("0"),
        )
        record2 = BorrowingRecord(
            borrowing_id="BORROW-002",
            currency="EUR",
            amount_base_ccy=Decimal("2000000"),
            purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
            treatment=BorrowingTreatment.REINVESTED,
            is_temporary=False,
            is_secured=True,
            reinvested_amount_base_ccy=Decimal("2000000"),
        )

        result = engine.calculate([record1, record2])

        for src in result.source_contributions:
            assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE
            assert src.exclusion_reason is None

    def test_multiple_partially_reinvested(self, engine):
        """Multiple partially reinvested records aggregate correctly."""
        records = [
            BorrowingRecord(
                borrowing_id=f"BORROW-{i:03d}",
                currency="EUR",
                amount_base_ccy=Decimal("1000000"),
                purpose=BorrowingPurpose.INVESTMENT_LEVERAGE,
                treatment=BorrowingTreatment.PARTIALLY_REINVESTED,
                is_temporary=False,
                is_secured=True,
                reinvested_amount_base_ccy=Decimal("600000"),
            )
            for i in range(1, 4)
        ]

        result = engine.calculate(records)

        sources = {src.source: src for src in result.source_contributions}
        assert sources[LeverageSource.DIRECT_BORROWING].gross_exposure == Decimal("1200000")
        assert sources[LeverageSource.REINVESTED_BORROWING].gross_exposure == Decimal("1800000")
