"""Tests for SFT leverage exposure engine.

Validates SFT record models and exposure calculation for repo, reverse repo,
and securities lending sources.
"""

from decimal import Decimal

import pytest

from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
)
from manco_risk.risk.leverage.sft_engine import SFTExposureEngine
from manco_risk.risk.leverage.sft_models import SFTRecord, SFTTreatment, SFTType


class TestSFTTypeEnum:
    """Test SFTType enum."""

    def test_sft_type_values_exist(self):
        """All required SFT types are defined."""
        assert SFTType.REPO.value == "REPO"
        assert SFTType.REVERSE_REPO.value == "REVERSE_REPO"
        assert SFTType.SECURITIES_LENDING.value == "SECURITIES_LENDING"

    def test_sft_type_count(self):
        """All expected SFT types are present."""
        assert len(list(SFTType)) == 3


class TestSFTTreatmentEnum:
    """Test SFTTreatment enum."""

    def test_sft_treatment_values_exist(self):
        """All required SFT treatments are defined."""
        assert SFTTreatment.CASH_COLLATERAL_REINVESTED.value == "CASH_COLLATERAL_REINVESTED"
        assert SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED.value == "CASH_COLLATERAL_NOT_REINVESTED"
        assert SFTTreatment.SECURITIES_COLLATERAL.value == "SECURITIES_COLLATERAL"
        assert SFTTreatment.OTHER.value == "OTHER"

    def test_sft_treatment_count(self):
        """All expected SFT treatments are present."""
        assert len(list(SFTTreatment)) == 4


class TestSFTRecord:
    """Test SFTRecord model."""

    def test_valid_repo_record(self):
        """Valid repo record."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )
        assert record.sft_id == "REPO-001"
        assert record.sft_type == SFTType.REPO
        assert record.market_value_base_ccy == Decimal("10000000")

    def test_valid_reverse_repo_record(self):
        """Valid reverse repo record."""
        record = SFTRecord(
            sft_id="REVERSE-001",
            sft_type=SFTType.REVERSE_REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("5000000"),
            cash_collateral_base_ccy=Decimal("0"),
            securities_collateral_base_ccy=Decimal("5200000"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.SECURITIES_COLLATERAL,
        )
        assert record.sft_type == SFTType.REVERSE_REPO
        assert record.securities_collateral_base_ccy == Decimal("5200000")

    def test_valid_securities_lending_record(self):
        """Valid securities lending record."""
        record = SFTRecord(
            sft_id="LEND-001",
            sft_type=SFTType.SECURITIES_LENDING,
            currency="EUR",
            market_value_base_ccy=Decimal("3000000"),
            cash_collateral_base_ccy=Decimal("3100000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
        )
        assert record.sft_type == SFTType.SECURITIES_LENDING
        assert record.reinvested_cash_collateral_base_ccy == Decimal("0")

    def test_rejects_empty_sft_id(self):
        """SFT ID cannot be empty."""
        with pytest.raises(ValueError, match="sft_id must be non-empty"):
            SFTRecord(
                sft_id="",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("5000000"),
                treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
            )

    def test_rejects_empty_currency(self):
        """Currency cannot be empty."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("5000000"),
                treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
            )

    def test_rejects_negative_market_value(self):
        """Market value cannot be negative."""
        with pytest.raises(ValueError, match="market_value_base_ccy must be non-negative"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("-100000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("5000000"),
                treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
            )

    def test_rejects_negative_cash_collateral(self):
        """Cash collateral cannot be negative."""
        with pytest.raises(ValueError, match="cash_collateral_base_ccy must be non-negative"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("-100000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("0"),
                treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
            )

    def test_rejects_negative_securities_collateral(self):
        """Securities collateral cannot be negative."""
        with pytest.raises(ValueError, match="securities_collateral_base_ccy must be non-negative"):
            SFTRecord(
                sft_id="REVERSE-001",
                sft_type=SFTType.REVERSE_REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("5000000"),
                cash_collateral_base_ccy=Decimal("0"),
                securities_collateral_base_ccy=Decimal("-100000"),
                reinvested_cash_collateral_base_ccy=Decimal("0"),
                treatment=SFTTreatment.SECURITIES_COLLATERAL,
            )

    def test_rejects_negative_reinvested_cash_collateral(self):
        """Reinvested cash collateral cannot be negative."""
        with pytest.raises(
            ValueError, match="reinvested_cash_collateral_base_ccy must be non-negative"
        ):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("-100000"),
                treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
            )

    def test_rejects_reinvested_greater_than_cash(self):
        """Reinvested cash collateral cannot exceed total cash collateral."""
        with pytest.raises(ValueError, match="cannot exceed cash_collateral_base_ccy"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("5000000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("6000000"),
                treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
            )

    def test_reinvested_treatment_requires_positive_reinvested(self):
        """CASH_COLLATERAL_REINVESTED requires positive reinvested amount."""
        with pytest.raises(ValueError, match="CASH_COLLATERAL_REINVESTED treatment requires"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("0"),
                treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
            )

    def test_not_reinvested_treatment_requires_zero_reinvested(self):
        """CASH_COLLATERAL_NOT_REINVESTED requires zero reinvested amount."""
        with pytest.raises(ValueError, match="CASH_COLLATERAL_NOT_REINVESTED treatment requires"):
            SFTRecord(
                sft_id="REPO-001",
                sft_type=SFTType.REPO,
                currency="EUR",
                market_value_base_ccy=Decimal("10000000"),
                cash_collateral_base_ccy=Decimal("9500000"),
                securities_collateral_base_ccy=Decimal("0"),
                reinvested_cash_collateral_base_ccy=Decimal("5000000"),
                treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
            )

    def test_model_is_frozen(self):
        """Model is immutable."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )
        with pytest.raises(Exception):  # Pydantic raises on frozen model
            record.sft_id = "REPO-002"


class TestSFTExposureEngine:
    """Test SFT exposure calculation."""

    @pytest.fixture
    def engine(self):
        """SFT exposure engine."""
        return SFTExposureEngine()

    def test_empty_sft_records(self, engine):
        """Empty SFT records return empty source contributions."""
        result = engine.calculate([])

        assert len(result.sft_records) == 0
        assert len(result.source_contributions) == 0
        assert len(result.warnings) == 0

    def test_repo_creates_sft_repo_source(self, engine):
        """Repo creates SFT_REPO source contribution."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 1
        src = result.source_contributions[0]
        assert src.source == LeverageSource.SFT_REPO
        assert src.commitment_exposure is None
        assert src.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_reverse_repo_creates_reverse_repo_source(self, engine):
        """Reverse repo creates SFT_REVERSE_REPO source contribution."""
        record = SFTRecord(
            sft_id="REVERSE-001",
            sft_type=SFTType.REVERSE_REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("5000000"),
            cash_collateral_base_ccy=Decimal("0"),
            securities_collateral_base_ccy=Decimal("5200000"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.SECURITIES_COLLATERAL,
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 1
        src = result.source_contributions[0]
        assert src.source == LeverageSource.SFT_REVERSE_REPO

    def test_securities_lending_creates_securities_lending_source(self, engine):
        """Securities lending creates SECURITIES_LENDING source contribution."""
        record = SFTRecord(
            sft_id="LEND-001",
            sft_type=SFTType.SECURITIES_LENDING,
            currency="EUR",
            market_value_base_ccy=Decimal("3000000"),
            cash_collateral_base_ccy=Decimal("3100000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
        )

        result = engine.calculate([record])

        assert len(result.source_contributions) == 1
        src = result.source_contributions[0]
        assert src.source == LeverageSource.SECURITIES_LENDING

    def test_reinvested_cash_increases_exposure(self, engine):
        """Reinvested cash collateral increases source-layer gross exposure."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )

        result = engine.calculate([record])

        src = result.source_contributions[0]
        expected_exposure = Decimal("10000000") + Decimal("5000000")
        assert src.gross_exposure == expected_exposure

    def test_non_reinvested_cash_does_not_increase_exposure(self, engine):
        """Non-reinvested cash collateral does not increase gross exposure."""
        record = SFTRecord(
            sft_id="LEND-001",
            sft_type=SFTType.SECURITIES_LENDING,
            currency="EUR",
            market_value_base_ccy=Decimal("3000000"),
            cash_collateral_base_ccy=Decimal("3100000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
        )

        result = engine.calculate([record])

        src = result.source_contributions[0]
        assert src.gross_exposure == Decimal("3000000")

    def test_securities_collateral_does_not_increase_exposure(self, engine):
        """Securities collateral does not increase Phase 1 gross exposure."""
        record = SFTRecord(
            sft_id="REVERSE-001",
            sft_type=SFTType.REVERSE_REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("5000000"),
            cash_collateral_base_ccy=Decimal("0"),
            securities_collateral_base_ccy=Decimal("5200000"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.SECURITIES_COLLATERAL,
        )

        result = engine.calculate([record])

        src = result.source_contributions[0]
        assert src.gross_exposure == Decimal("5000000")

    def test_multiple_records_aggregate_by_source(self, engine):
        """Multiple records aggregate exposures by source."""
        repo1 = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("5000000"),
            cash_collateral_base_ccy=Decimal("4500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("2000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )
        repo2 = SFTRecord(
            sft_id="REPO-002",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("3000000"),
            cash_collateral_base_ccy=Decimal("2800000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("1500000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )
        reverse = SFTRecord(
            sft_id="REVERSE-001",
            sft_type=SFTType.REVERSE_REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("4000000"),
            cash_collateral_base_ccy=Decimal("0"),
            securities_collateral_base_ccy=Decimal("4200000"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.SECURITIES_COLLATERAL,
        )

        result = engine.calculate([repo1, repo2, reverse])

        sources = {src.source: src for src in result.source_contributions}
        assert len(sources) == 2

        repo_src = sources[LeverageSource.SFT_REPO]
        reverse_src = sources[LeverageSource.SFT_REVERSE_REPO]

        expected_repo = (Decimal("5000000") + Decimal("2000000")) + (
            Decimal("3000000") + Decimal("1500000")
        )
        assert repo_src.gross_exposure == expected_repo
        assert reverse_src.gross_exposure == Decimal("4000000")

    def test_commitment_exposure_none(self, engine):
        """Commitment exposure is None at source layer."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )

        result = engine.calculate([record])

        assert result.source_contributions[0].commitment_exposure is None

    def test_treatment_pending_method_rule(self, engine):
        """Treatment is PENDING_METHOD_RULE."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )

        result = engine.calculate([record])

        assert result.source_contributions[0].treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_no_warnings_on_valid_records(self, engine):
        """Valid SFT records produce no warnings."""
        record = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("10000000"),
            cash_collateral_base_ccy=Decimal("9500000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("5000000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )

        result = engine.calculate([record])

        assert len(result.warnings) == 0

    def test_result_model_is_frozen(self, engine):
        """Result model is immutable."""
        result = engine.calculate([])

        with pytest.raises(Exception):  # Pydantic raises on frozen model
            result.source_contributions = []

    def test_all_sft_types_create_sources(self, engine):
        """All SFT types create appropriate source contributions."""
        repo = SFTRecord(
            sft_id="REPO-001",
            sft_type=SFTType.REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("1000000"),
            cash_collateral_base_ccy=Decimal("900000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("500000"),
            treatment=SFTTreatment.CASH_COLLATERAL_REINVESTED,
        )
        reverse = SFTRecord(
            sft_id="REVERSE-001",
            sft_type=SFTType.REVERSE_REPO,
            currency="EUR",
            market_value_base_ccy=Decimal("500000"),
            cash_collateral_base_ccy=Decimal("0"),
            securities_collateral_base_ccy=Decimal("520000"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.SECURITIES_COLLATERAL,
        )
        lending = SFTRecord(
            sft_id="LEND-001",
            sft_type=SFTType.SECURITIES_LENDING,
            currency="EUR",
            market_value_base_ccy=Decimal("750000"),
            cash_collateral_base_ccy=Decimal("800000"),
            securities_collateral_base_ccy=Decimal("0"),
            reinvested_cash_collateral_base_ccy=Decimal("0"),
            treatment=SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED,
        )

        result = engine.calculate([repo, reverse, lending])

        assert len(result.source_contributions) == 3
        sources = {src.source for src in result.source_contributions}
        assert sources == {
            LeverageSource.SFT_REPO,
            LeverageSource.SFT_REVERSE_REPO,
            LeverageSource.SECURITIES_LENDING,
        }
