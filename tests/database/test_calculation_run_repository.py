"""Tests for CalculationRunRepository."""

from datetime import date, datetime

from manco_risk.database.models import CalculationRun, CalculationStatusEnum, CalculationTypeEnum
from manco_risk.database.repositories import CalculationRunRepository
from manco_risk.database.session import SessionFactory


class TestCalculationRunRepository:
    """Test CalculationRunRepository CRUD and query methods."""

    def test_insert_calculation_run(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Insert a calculation run and verify it's persisted."""
        repo = CalculationRunRepository(session_factory)

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

        inserted = repo.insert(calc_run)

        assert inserted.calculation_run_id is not None
        assert inserted.fund_id == sample_fund.fund_id
        assert inserted.valuation_date == date(2024, 1, 1)
        assert inserted.calculation_type == CalculationTypeEnum.VAR_ES_DAILY
        assert inserted.status == CalculationStatusEnum.COMPLETED

    def test_find_by_id(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Find a calculation run by ID."""
        repo = CalculationRunRepository(session_factory)

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
        inserted = repo.insert(calc_run)

        found = repo.find_by_id(inserted.calculation_run_id)

        assert found is not None
        assert found.calculation_run_id == inserted.calculation_run_id
        assert found.fund_id == sample_fund.fund_id

    def test_find_by_id_not_found(self, session_factory: SessionFactory) -> None:
        """Find by ID returns None for non-existent ID."""
        repo = CalculationRunRepository(session_factory)
        found = repo.find_by_id(99999)
        assert found is None

    def test_find_by_fund_and_date(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Find calculation runs by fund and date."""
        repo = CalculationRunRepository(session_factory)

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
        repo.insert(calc_run1)

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
        repo.insert(calc_run2)

        found = repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(found) == 1
        assert found[0].valuation_date == date(2024, 1, 1)
        assert found[0].fund_id == sample_fund.fund_id

    def test_find_by_fund_and_date_empty(
        self, session_factory: SessionFactory, sample_fund
    ) -> None:
        """Find by fund and date returns empty list when no results."""
        repo = CalculationRunRepository(session_factory)
        found = repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert found == []
