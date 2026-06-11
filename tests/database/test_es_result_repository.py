"""Tests for ExpectedShortfallResultRepository."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from manco_risk.database.models import (
    CalculationRun,
    CalculationStatusEnum,
    CalculationTypeEnum,
    ESMethodEnum,
    ExpectedShortfallResult,
)
from manco_risk.database.repositories import (
    CalculationRunRepository,
    ExpectedShortfallResultRepository,
)
from manco_risk.database.session import SessionFactory


class TestExpectedShortfallResultRepository:
    """Test ExpectedShortfallResultRepository CRUD and query methods."""

    def test_insert_es_result(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Insert an ES result and verify it's persisted."""
        # Create calculation run first
        calc_repo = CalculationRunRepository(session_factory)
        calc_run = CalculationRun(
            fund_id=sample_fund.fund_id,
            valuation_date=date(2024, 1, 1),
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=sample_risk_methodology.methodology_version_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            status=CalculationStatusEnum.COMPLETED,
            created_by="test_user",
        )
        inserted_run = calc_repo.insert(calc_run)

        # Create and insert ES result
        es_result = ExpectedShortfallResult(
            calculation_run_id=inserted_run.calculation_run_id,
            fund_id=sample_fund.fund_id,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value_absolute=Decimal("3500.00"),
            es_pct_nav=Decimal("0.035"),
            method=ESMethodEnum.HISTORICAL,
            num_breaches=25,
            num_observations_used=250,
        )
        es_repo = ExpectedShortfallResultRepository(session_factory)
        inserted = es_repo.insert(es_result)

        assert inserted.es_result_id is not None
        assert inserted.calculation_run_id == inserted_run.calculation_run_id
        assert inserted.fund_id == sample_fund.fund_id
        assert inserted.confidence_level == Decimal("0.95")
        assert inserted.es_value_absolute == Decimal("3500.00")
        assert inserted.method == ESMethodEnum.HISTORICAL

    def test_find_by_calculation_run(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Find ES results by calculation run ID."""
        # Create calculation run
        calc_repo = CalculationRunRepository(session_factory)
        calc_run = CalculationRun(
            fund_id=sample_fund.fund_id,
            valuation_date=date(2024, 1, 1),
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=sample_risk_methodology.methodology_version_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            status=CalculationStatusEnum.COMPLETED,
            created_by="test_user",
        )
        inserted_run = calc_repo.insert(calc_run)

        # Create and insert multiple ES results
        es_repo = ExpectedShortfallResultRepository(session_factory)
        for conf_level in [Decimal("0.90"), Decimal("0.95"), Decimal("0.99")]:
            es_result = ExpectedShortfallResult(
                calculation_run_id=inserted_run.calculation_run_id,
                fund_id=sample_fund.fund_id,
                confidence_level=conf_level,
                horizon_days=1,
                es_value_absolute=Decimal("3500.00"),
                es_pct_nav=Decimal("0.035"),
                method=ESMethodEnum.HISTORICAL,
                num_breaches=25,
                num_observations_used=250,
            )
            es_repo.insert(es_result)

        # Find all results for this calculation run
        found = es_repo.find_by_calculation_run(inserted_run.calculation_run_id)

        assert len(found) == 3
        assert all(r.calculation_run_id == inserted_run.calculation_run_id for r in found)

    def test_find_by_calculation_run_empty(self, session_factory: SessionFactory) -> None:
        """Find by calculation run returns empty list when no results exist."""
        es_repo = ExpectedShortfallResultRepository(session_factory)
        found = es_repo.find_by_calculation_run(99999)
        assert found == []

    def test_find_by_fund_and_date(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Find ES results by fund and valuation date."""
        # Create two calculation runs on different dates
        calc_repo = CalculationRunRepository(session_factory)

        calc_run1 = CalculationRun(
            fund_id=sample_fund.fund_id,
            valuation_date=date(2024, 1, 1),
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=sample_risk_methodology.methodology_version_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            status=CalculationStatusEnum.COMPLETED,
            created_by="test_user",
        )
        inserted_run1 = calc_repo.insert(calc_run1)

        calc_run2 = CalculationRun(
            fund_id=sample_fund.fund_id,
            valuation_date=date(2024, 1, 2),
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=sample_risk_methodology.methodology_version_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            status=CalculationStatusEnum.COMPLETED,
            created_by="test_user",
        )
        inserted_run2 = calc_repo.insert(calc_run2)

        # Create ES results for both runs
        es_repo = ExpectedShortfallResultRepository(session_factory)
        es_result1 = ExpectedShortfallResult(
            calculation_run_id=inserted_run1.calculation_run_id,
            fund_id=sample_fund.fund_id,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value_absolute=Decimal("3500.00"),
            es_pct_nav=Decimal("0.035"),
            method=ESMethodEnum.HISTORICAL,
            num_breaches=25,
            num_observations_used=250,
        )
        es_repo.insert(es_result1)

        es_result2 = ExpectedShortfallResult(
            calculation_run_id=inserted_run2.calculation_run_id,
            fund_id=sample_fund.fund_id,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value_absolute=Decimal("3600.00"),
            es_pct_nav=Decimal("0.036"),
            method=ESMethodEnum.HISTORICAL,
            num_breaches=25,
            num_observations_used=250,
        )
        es_repo.insert(es_result2)

        # Find by fund and date 2024-01-01
        found = es_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(found) == 1
        assert found[0].es_value_absolute == Decimal("3500.00")

    def test_find_by_fund_and_date_empty(
        self, session_factory: SessionFactory, sample_fund
    ) -> None:
        """Find by fund and date returns empty list when no results exist."""
        es_repo = ExpectedShortfallResultRepository(session_factory)
        found = es_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert found == []

    def test_unique_constraint_calculation_run_confidence_horizon(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Unique constraint on (calculation_run_id, confidence_level, horizon_days) is enforced."""
        # Create calculation run
        calc_repo = CalculationRunRepository(session_factory)
        calc_run = CalculationRun(
            fund_id=sample_fund.fund_id,
            valuation_date=date(2024, 1, 1),
            calculation_type=CalculationTypeEnum.VAR_ES_DAILY,
            created_timestamp=datetime.now(),
            methodology_version_id=sample_risk_methodology.methodology_version_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            status=CalculationStatusEnum.COMPLETED,
            created_by="test_user",
        )
        inserted_run = calc_repo.insert(calc_run)

        # Insert first ES result
        es_repo = ExpectedShortfallResultRepository(session_factory)
        es_result1 = ExpectedShortfallResult(
            calculation_run_id=inserted_run.calculation_run_id,
            fund_id=sample_fund.fund_id,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value_absolute=Decimal("3500.00"),
            es_pct_nav=Decimal("0.035"),
            method=ESMethodEnum.HISTORICAL,
            num_breaches=25,
            num_observations_used=250,
        )
        es_repo.insert(es_result1)

        # Attempt to insert duplicate (same calculation_run_id, confidence_level, horizon_days)
        es_result2 = ExpectedShortfallResult(
            calculation_run_id=inserted_run.calculation_run_id,
            fund_id=sample_fund.fund_id,
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            es_value_absolute=Decimal("3600.00"),  # Different value
            es_pct_nav=Decimal("0.036"),
            method=ESMethodEnum.HISTORICAL,
            num_breaches=25,
            num_observations_used=250,
        )

        with pytest.raises(Exception):  # SQLAlchemy integrity error
            es_repo.insert(es_result2)
