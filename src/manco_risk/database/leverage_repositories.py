"""Repositories for leverage calculation results.

Handles persistence and retrieval of leverage results from the database.
"""

from datetime import date
from typing import Optional

from sqlalchemy import desc, select

from manco_risk.database.models import (
    LeverageResult,
    LeverageSourceContributionResult,
)
from manco_risk.database.session import SessionFactory


class LeverageResultRepository:
    """Repository for LeverageResult ORM entity.

    Handles insert, update, and query operations on leverage results.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize repository with session factory.

        Parameters
        ----------
        session_factory : SessionFactory
            Session factory for database access.
        """
        self.session_factory = session_factory

    def insert(self, leverage_result: LeverageResult) -> int:
        """Insert a single leverage result.

        Parameters
        ----------
        leverage_result : LeverageResult
            Leverage result ORM model to persist.

        Returns
        -------
        int
            Primary key of inserted result.
        """
        with self.session_factory.session_scope() as session:
            session.add(leverage_result)
            session.flush()
            result_id = leverage_result.leverage_result_id
            return result_id

    def insert_many(self, leverage_results: list[LeverageResult]) -> list[int]:
        """Insert multiple leverage results.

        Parameters
        ----------
        leverage_results : list[LeverageResult]
            List of leverage result ORM models to persist.

        Returns
        -------
        list[int]
            List of primary keys of inserted results.
        """
        with self.session_factory.session_scope() as session:
            session.add_all(leverage_results)
            session.flush()
            result_ids = [lr.leverage_result_id for lr in leverage_results]
            return result_ids

    def get_by_calculation_run_id(self, calculation_run_id: int) -> list[LeverageResult]:
        """Get all leverage results for a calculation run.

        Parameters
        ----------
        calculation_run_id : int
            Calculation run ID to filter by.

        Returns
        -------
        list[LeverageResult]
            Leverage results for the given calculation run.
        """
        with self.session_factory.session_scope() as session:
            stmt = select(LeverageResult).where(
                LeverageResult.calculation_run_id == calculation_run_id
            )
            return list(session.execute(stmt).scalars().all())

    def get_latest_by_fund_id(self, fund_id: int) -> Optional[LeverageResult]:
        """Get latest leverage result for a fund (most recent valuation date).

        Parameters
        ----------
        fund_id : int
            Fund ID to filter by.

        Returns
        -------
        Optional[LeverageResult]
            Latest leverage result, or None if none exist.
        """
        with self.session_factory.session_scope() as session:
            stmt = (
                select(LeverageResult)
                .where(LeverageResult.fund_id == fund_id)
                .order_by(desc(LeverageResult.valuation_date))
                .limit(1)
            )
            return session.execute(stmt).scalar()

    def get_by_fund_and_date(self, fund_id: int, valuation_date: date) -> list[LeverageResult]:
        """Get all leverage results for a fund on a given valuation date.

        Parameters
        ----------
        fund_id : int
            Fund ID to filter by.
        valuation_date : date
            Valuation date to filter by.

        Returns
        -------
        list[LeverageResult]
            Leverage results for the given fund and date.
        """
        with self.session_factory.session_scope() as session:
            stmt = select(LeverageResult).where(
                (LeverageResult.fund_id == fund_id)
                & (LeverageResult.valuation_date == valuation_date)
            )
            return list(session.execute(stmt).scalars().all())

    def get_by_id(self, leverage_result_id: int) -> Optional[LeverageResult]:
        """Get a leverage result by ID.

        Parameters
        ----------
        leverage_result_id : int
            Leverage result ID.

        Returns
        -------
        Optional[LeverageResult]
            Leverage result, or None if not found.
        """
        with self.session_factory.session_scope() as session:
            return session.get(LeverageResult, leverage_result_id)


class LeverageSourceContributionResultRepository:
    """Repository for LeverageSourceContributionResult ORM entity.

    Handles persistence and retrieval of source contribution breakdowns.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        """Initialize repository with session factory.

        Parameters
        ----------
        session_factory : SessionFactory
            Session factory for database access.
        """
        self.session_factory = session_factory

    def insert_many(self, contributions: list[LeverageSourceContributionResult]) -> list[int]:
        """Insert multiple source contributions.

        Parameters
        ----------
        contributions : list[LeverageSourceContributionResult]
            List of source contribution ORM models to persist.

        Returns
        -------
        list[int]
            List of primary keys of inserted contributions.
        """
        with self.session_factory.session_scope() as session:
            session.add_all(contributions)
            session.flush()
            contrib_ids = [c.source_contribution_result_id for c in contributions]
            return contrib_ids

    def get_by_leverage_result_id(
        self, leverage_result_id: int
    ) -> list[LeverageSourceContributionResult]:
        """Get all source contributions for a leverage result.

        Parameters
        ----------
        leverage_result_id : int
            Leverage result ID to filter by.

        Returns
        -------
        list[LeverageSourceContributionResult]
            Source contributions for the given leverage result.
        """
        with self.session_factory.session_scope() as session:
            stmt = select(LeverageSourceContributionResult).where(
                LeverageSourceContributionResult.leverage_result_id == leverage_result_id
            )
            return list(session.execute(stmt).scalars().all())
