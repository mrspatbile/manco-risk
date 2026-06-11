"""Tests for leverage result repositories.

Validates persistence and retrieval of leverage results.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.database.leverage_repositories import (
    LeverageResultRepository,
    LeverageSourceContributionResultRepository,
)
from manco_risk.database.models import (
    LeverageResult,
    LeverageSourceContributionResult,
)
from manco_risk.database.session import SessionFactory


@pytest.fixture
def leverage_result():
    """Create a leverage result ORM model."""
    return LeverageResult(
        calculation_run_id=1,
        fund_id=1,
        valuation_date=date(2026, 6, 11),
        method="AIFMD_GROSS",
        nav=Decimal("10000000"),
        total_exposure=Decimal("6500000"),
        leverage_ratio=Decimal("0.65"),
        base_exposure_before_reductions=None,
        total_reductions=None,
        final_exposure=None,
        num_applied_reductions=0,
        num_ignored_reductions=0,
        warnings="Warning 1\nWarning 2",
    )


@pytest.fixture
def commitment_leverage_result():
    """Create a commitment leverage result ORM model."""
    return LeverageResult(
        calculation_run_id=1,
        fund_id=1,
        valuation_date=date(2026, 6, 11),
        method="AIFMD_COMMITMENT",
        nav=Decimal("10000000"),
        total_exposure=Decimal("4500000"),
        leverage_ratio=Decimal("0.45"),
        base_exposure_before_reductions=Decimal("5000000"),
        total_reductions=Decimal("500000"),
        final_exposure=Decimal("4500000"),
        num_applied_reductions=1,
        num_ignored_reductions=0,
        warnings=None,
    )


class TestLeverageResultRepository:
    """Test LeverageResultRepository persistence and retrieval."""

    def test_insert_leverage_result(self, session_factory: SessionFactory, leverage_result):
        """Insert a leverage result and verify it's persisted."""
        repo = LeverageResultRepository(session_factory)
        result_id = repo.insert(leverage_result)

        assert result_id is not None
        assert result_id > 0

        # Retrieve and verify
        retrieved = repo.get_by_id(result_id)
        assert retrieved is not None
        assert retrieved.leverage_result_id == result_id
        assert retrieved.method == "AIFMD_GROSS"
        assert retrieved.nav == Decimal("10000000")
        assert retrieved.total_exposure == Decimal("6500000")

    def test_insert_many_leverage_results(
        self, session_factory: SessionFactory, leverage_result, commitment_leverage_result
    ):
        """Insert multiple leverage results."""
        repo = LeverageResultRepository(session_factory)
        results = [leverage_result, commitment_leverage_result]
        result_ids = repo.insert_many(results)

        assert len(result_ids) == 2
        assert all(rid > 0 for rid in result_ids)

        # Verify both were inserted
        for result_id in result_ids:
            retrieved = repo.get_by_id(result_id)
            assert retrieved is not None

    def test_get_by_calculation_run_id(
        self, session_factory: SessionFactory, leverage_result, commitment_leverage_result
    ):
        """Retrieve all leverage results for a calculation run."""
        repo = LeverageResultRepository(session_factory)
        repo.insert(leverage_result)
        repo.insert(commitment_leverage_result)

        results = repo.get_by_calculation_run_id(1)

        assert len(results) == 2
        methods = {r.method for r in results}
        assert methods == {"AIFMD_GROSS", "AIFMD_COMMITMENT"}

    def test_get_latest_by_fund_id(self, session_factory: SessionFactory):
        """Retrieve latest leverage result for a fund."""
        repo = LeverageResultRepository(session_factory)

        # Insert two results for the same fund on different dates
        result1 = LeverageResult(
            calculation_run_id=1,
            fund_id=1,
            valuation_date=date(2026, 6, 10),
            method="AIFMD_GROSS",
            nav=Decimal("10000000"),
            total_exposure=Decimal("6500000"),
            leverage_ratio=Decimal("0.65"),
            warnings=None,
        )
        result2 = LeverageResult(
            calculation_run_id=2,
            fund_id=1,
            valuation_date=date(2026, 6, 11),
            method="AIFMD_GROSS",
            nav=Decimal("10500000"),
            total_exposure=Decimal("6800000"),
            leverage_ratio=Decimal("0.648"),
            warnings=None,
        )

        repo.insert(result1)
        repo.insert(result2)

        latest = repo.get_latest_by_fund_id(1)

        assert latest is not None
        assert latest.valuation_date == date(2026, 6, 11)
        assert latest.nav == Decimal("10500000")

    def test_get_by_fund_and_date(
        self, session_factory: SessionFactory, leverage_result, commitment_leverage_result
    ):
        """Retrieve all leverage results for a fund on a specific date."""
        repo = LeverageResultRepository(session_factory)
        repo.insert(leverage_result)
        repo.insert(commitment_leverage_result)

        results = repo.get_by_fund_and_date(fund_id=1, valuation_date=date(2026, 6, 11))

        assert len(results) == 2
        methods = {r.method for r in results}
        assert methods == {"AIFMD_GROSS", "AIFMD_COMMITMENT"}

    def test_get_by_fund_and_date_no_results(self, session_factory: SessionFactory):
        """Return empty list when no results for given fund/date."""
        repo = LeverageResultRepository(session_factory)

        results = repo.get_by_fund_and_date(fund_id=999, valuation_date=date(2026, 6, 11))

        assert results == []

    def test_get_by_id_not_found(self, session_factory: SessionFactory):
        """Return None when leverage result not found."""
        repo = LeverageResultRepository(session_factory)

        result = repo.get_by_id(999999)

        assert result is None


class TestLeverageSourceContributionResultRepository:
    """Test LeverageSourceContributionResultRepository persistence and retrieval."""

    def test_insert_source_contributions(self, session_factory: SessionFactory):
        """Insert and retrieve source contribution results."""
        # First create and insert a leverage result
        leverage_repo = LeverageResultRepository(session_factory)
        leverage_result = LeverageResult(
            calculation_run_id=1,
            fund_id=1,
            valuation_date=date(2026, 6, 11),
            method="AIFMD_GROSS",
            nav=Decimal("10000000"),
            total_exposure=Decimal("6500000"),
            leverage_ratio=Decimal("0.65"),
            warnings=None,
        )
        leverage_result_id = leverage_repo.insert(leverage_result)

        # Then insert source contributions
        contrib_repo = LeverageSourceContributionResultRepository(session_factory)
        contributions = [
            LeverageSourceContributionResult(
                leverage_result_id=leverage_result_id,
                source="PHYSICAL_INSTRUMENT",
                gross_exposure=Decimal("5000000"),
                commitment_exposure=Decimal("5000000"),
                treatment="INCLUDED",
                exclusion_reason=None,
                percentage_of_nav=Decimal("0.50"),
            ),
            LeverageSourceContributionResult(
                leverage_result_id=leverage_result_id,
                source="DERIVATIVE",
                gross_exposure=Decimal("1500000"),
                commitment_exposure=None,
                treatment="PENDING_METHOD_RULE",
                exclusion_reason=None,
                percentage_of_nav=Decimal("0.15"),
            ),
        ]

        contrib_ids = contrib_repo.insert_many(contributions)
        assert len(contrib_ids) == 2

    def test_get_by_leverage_result_id(self, session_factory: SessionFactory, leverage_result):
        """Retrieve all source contributions for a leverage result."""
        # Insert leverage result
        leverage_repo = LeverageResultRepository(session_factory)
        leverage_result_id = leverage_repo.insert(leverage_result)

        # Insert source contributions
        contrib_repo = LeverageSourceContributionResultRepository(session_factory)
        contributions = [
            LeverageSourceContributionResult(
                leverage_result_id=leverage_result_id,
                source="PHYSICAL_INSTRUMENT",
                gross_exposure=Decimal("5000000"),
                commitment_exposure=Decimal("5000000"),
                treatment="INCLUDED",
                exclusion_reason=None,
                percentage_of_nav=Decimal("0.50"),
            ),
            LeverageSourceContributionResult(
                leverage_result_id=leverage_result_id,
                source="CASH_AND_CASH_EQUIVALENT",
                gross_exposure=Decimal("0"),
                commitment_exposure=Decimal("0"),
                treatment="EXCLUDED",
                exclusion_reason="Cash excluded",
                percentage_of_nav=Decimal("0.00"),
            ),
        ]
        contrib_repo.insert_many(contributions)

        # Retrieve
        retrieved = contrib_repo.get_by_leverage_result_id(leverage_result_id)

        assert len(retrieved) == 2
        sources = {c.source for c in retrieved}
        assert sources == {"PHYSICAL_INSTRUMENT", "CASH_AND_CASH_EQUIVALENT"}

    def test_get_by_leverage_result_id_no_contributions(self, session_factory: SessionFactory):
        """Return empty list when no contributions exist."""
        repo = LeverageSourceContributionResultRepository(session_factory)

        contributions = repo.get_by_leverage_result_id(999999)

        assert contributions == []
