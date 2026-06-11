"""Tests for VaR calculation services.

Tests orchestration of VaR calculation and persistence workflows.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.database.models import CalculationStatusEnum
from manco_risk.database.repositories import (
    CalculationRunRepository,
    VaRResultRepository,
)
from manco_risk.database.session import SessionFactory
from manco_risk.database.var_calculation_service import (
    HistoricalVaRCalculationService,
    ParametricNormalVaRCalculationService,
)
from manco_risk.etl.enriched_position import EnrichedPosition, RiskReadyPortfolio
from manco_risk.risk.exceptions import (
    InsufficientPriceDataError,
    MissingHistoricalDataError,
    UnsupportedAssetClassError,
)
from manco_risk.risk.models.price_return import PricePoint


class TestHistoricalVaRCalculationService:
    """Test HistoricalVaRCalculationService workflow."""

    def test_happy_path_calculate_and_persist(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Happy path: calculate VaR and persist CalculationRun + VaRResult."""
        service = HistoricalVaRCalculationService(session_factory)

        # Create enriched positions
        position1 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("60000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("60000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.6"),
        )

        position2 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=2,
            isin="IE00B4L5Y983",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("40000.00"),
            position_currency="EUR",
            asset_class="ETF",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("40000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.4"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position1, position2],
        )

        # Create price history (5 observations per ISIN)
        price_points = []
        for i in range(6):
            scenario_date = date(2024, 1, 1 + i)
            price_points.append(
                PricePoint(isin="US0378331005", price_date=scenario_date, price=Decimal("100"))
            )
            price_points.append(
                PricePoint(isin="IE00B4L5Y983", price_date=scenario_date, price=Decimal("100"))
            )

        # Calculate and persist
        result = service.calculate_and_persist_historical_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Verify in-memory result
        assert result.fund_id == sample_fund.fund_id
        assert result.confidence_level == Decimal("0.95")

        # Verify VaRResult persisted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) > 0
        assert var_results[0].fund_id == sample_fund.fund_id
        assert var_results[0].confidence_level == Decimal("0.95")
        assert var_results[0].var_value_absolute == result.var_value
        assert var_results[0].var_pct_nav == result.var_pct_nav

    def test_calculation_run_status_completed_on_success(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """CalculationRun status is COMPLETED after successful calculation."""
        service = HistoricalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        service.calculate_and_persist_historical_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Query all runs for this fund/date
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.COMPLETED

    def test_insufficient_price_data_marks_failed(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Insufficient prices: CalculationRun marked FAILED, VaRResult not inserted."""
        service = HistoricalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Only 1 price point (need at least 2 for returns)
        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100"))
        ]

        with pytest.raises(Exception):  # InsufficientPriceDataError
            service.calculate_and_persist_historical_var(
                portfolio=portfolio,
                historical_price_points=price_points,
                risk_methodology=sample_risk_methodology,
                position_snapshot_id=sample_position_snapshot.position_snapshot_id,
                nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
                created_by="test_user",
            )

        # Verify CalculationRun marked FAILED
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.FAILED

        # Verify no VaRResult inserted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) == 0

    def test_unsupported_asset_class_marks_failed(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Unsupported asset class: CalculationRun marked FAILED, VaRResult not inserted."""
        service = HistoricalVaRCalculationService(session_factory)

        # BOND is unsupported in Phase 1
        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="DE0001102309",
            valuation_date="2024-01-01",
            quantity=Decimal("500"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="BOND",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        price_points = [
            PricePoint(isin="DE0001102309", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        with pytest.raises(UnsupportedAssetClassError):
            service.calculate_and_persist_historical_var(
                portfolio=portfolio,
                historical_price_points=price_points,
                risk_methodology=sample_risk_methodology,
                position_snapshot_id=sample_position_snapshot.position_snapshot_id,
                nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
                created_by="test_user",
            )

        # Verify CalculationRun marked FAILED
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.FAILED

        # Verify no VaRResult inserted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) == 0

    def test_missing_return_data_marks_failed(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Missing return data for one position: CalculationRun marked FAILED."""
        service = HistoricalVaRCalculationService(session_factory)

        position1 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("50000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("50000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.5"),
        )

        position2 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=2,
            isin="IE00B4L5Y983",  # No price data for this ISIN
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("50000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("50000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.5"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position1, position2],
        )

        # Only prices for position1, missing position2
        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        with pytest.raises(MissingHistoricalDataError):
            service.calculate_and_persist_historical_var(
                portfolio=portfolio,
                historical_price_points=price_points,
                risk_methodology=sample_risk_methodology,
                position_snapshot_id=sample_position_snapshot.position_snapshot_id,
                nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
                created_by="test_user",
            )

        # Verify CalculationRun marked FAILED
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.FAILED

        # Verify no VaRResult inserted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) == 0

    def test_var_result_field_mapping(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """VaRResult fields match in-memory calculation result."""
        service = HistoricalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        var_result = service.calculate_and_persist_historical_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Retrieve persisted VaRResult
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(var_results) == 1
        orm_result = var_results[0]

        # Verify field mapping
        assert orm_result.fund_id == var_result.fund_id
        assert orm_result.confidence_level == var_result.confidence_level
        assert orm_result.horizon_days == var_result.horizon_days
        assert orm_result.var_value_absolute == var_result.var_value
        assert orm_result.var_pct_nav == var_result.var_pct_nav
        assert orm_result.num_observations_used == var_result.num_scenarios
        assert orm_result.lookback_days == sample_risk_methodology.var_lookback_days


class TestParametricNormalVaRCalculationService:
    """Test ParametricNormalVaRCalculationService workflow."""

    def test_happy_path_calculate_and_persist(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Happy path: calculate parametric VaR and persist CalculationRun + VaRResult."""
        service = ParametricNormalVaRCalculationService(session_factory)

        # Create enriched positions
        position1 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("60000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("60000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.6"),
        )

        position2 = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=2,
            isin="IE00B4L5Y983",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("40000.00"),
            position_currency="EUR",
            asset_class="ETF",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("40000.00"),
            fund_base_currency="EUR",
            weight=Decimal("0.4"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position1, position2],
        )

        # Create price history (6 observations per ISIN)
        price_points = []
        for i in range(6):
            scenario_date = date(2024, 1, 1 + i)
            price_points.append(
                PricePoint(isin="US0378331005", price_date=scenario_date, price=Decimal("100"))
            )
            price_points.append(
                PricePoint(isin="IE00B4L5Y983", price_date=scenario_date, price=Decimal("100"))
            )

        # Calculate and persist
        result = service.calculate_and_persist_parametric_normal_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Verify in-memory result
        assert result.fund_id == sample_fund.fund_id
        assert result.confidence_level == Decimal("0.95")

        # Verify VaRResult persisted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) > 0
        assert var_results[0].fund_id == sample_fund.fund_id
        assert var_results[0].confidence_level == Decimal("0.95")
        assert var_results[0].var_value_absolute == result.var_value
        assert var_results[0].var_pct_nav == result.var_pct_nav

    def test_calculation_run_status_completed_on_success(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """CalculationRun status is COMPLETED after successful parametric VaR calculation."""
        service = ParametricNormalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        service.calculate_and_persist_parametric_normal_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Query all runs for this fund/date
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.COMPLETED

    def test_insufficient_price_data_marks_failed(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """Insufficient prices: CalculationRun marked FAILED, VaRResult not inserted."""
        service = ParametricNormalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("400"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        # Only 1 price point; ParametricNormalVaRInput requires at least 2 for std dev
        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100"))
        ]

        with pytest.raises(InsufficientPriceDataError):
            service.calculate_and_persist_parametric_normal_var(
                portfolio=portfolio,
                historical_price_points=price_points,
                risk_methodology=sample_risk_methodology,
                position_snapshot_id=sample_position_snapshot.position_snapshot_id,
                nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
                created_by="test_user",
            )

        # Verify CalculationRun marked FAILED
        calc_repo = CalculationRunRepository(session_factory)
        runs = calc_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(runs) == 1
        assert runs[0].status == CalculationStatusEnum.FAILED

        # Verify no VaRResult inserted
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))
        assert len(var_results) == 0

    def test_var_result_field_mapping(
        self,
        session_factory: SessionFactory,
        sample_fund,
        sample_position_snapshot,
        sample_nav_snapshot,
        sample_risk_methodology,
    ) -> None:
        """VaRResult fields match in-memory parametric VaR calculation result."""
        service = ParametricNormalVaRCalculationService(session_factory)

        position = EnrichedPosition(
            fund_id=sample_fund.fund_id,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            position_id=1,
            isin="US0378331005",
            valuation_date="2024-01-01",
            quantity=Decimal("1000"),
            market_value=Decimal("100000.00"),
            position_currency="EUR",
            asset_class="EQUITY",
            instrument_currency="EUR",
            market_value_base_ccy=Decimal("100000.00"),
            fund_base_currency="EUR",
            weight=Decimal("1.0"),
        )

        portfolio = RiskReadyPortfolio(
            fund_id=sample_fund.fund_id,
            valuation_date="2024-01-01",
            fund_base_currency="EUR",
            nav=Decimal("100000.00"),
            positions=[position],
        )

        price_points = [
            PricePoint(isin="US0378331005", price_date=date(2024, 1, 1 + i), price=Decimal("100"))
            for i in range(6)
        ]

        var_result = service.calculate_and_persist_parametric_normal_var(
            portfolio=portfolio,
            historical_price_points=price_points,
            risk_methodology=sample_risk_methodology,
            position_snapshot_id=sample_position_snapshot.position_snapshot_id,
            nav_snapshot_id=sample_nav_snapshot.nav_snapshot_id,
            created_by="test_user",
        )

        # Retrieve persisted VaRResult
        var_repo = VaRResultRepository(session_factory)
        var_results = var_repo.find_by_fund_and_date(sample_fund.fund_id, date(2024, 1, 1))

        assert len(var_results) == 1
        orm_result = var_results[0]

        # Verify field mapping
        assert orm_result.fund_id == var_result.fund_id
        assert orm_result.confidence_level == var_result.confidence_level
        assert orm_result.horizon_days == var_result.horizon_days
        assert orm_result.var_value_absolute == var_result.var_value
        assert orm_result.var_pct_nav == var_result.var_pct_nav
        assert orm_result.num_observations_used == var_result.num_observations
        assert orm_result.lookback_days == sample_risk_methodology.var_lookback_days
