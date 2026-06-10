"""Tests for var_mappers module."""

from datetime import date
from decimal import Decimal

from manco_risk.database.var_mappers import map_historical_var_result_to_orm
from manco_risk.risk.models.var_result import HistoricalVaRResult


class TestMapHistoricalVaRResultToOrm:
    """Test mapping from HistoricalVaRResult to ORM VaRResult."""

    def test_map_all_fields(self) -> None:
        """Map all fields from Pydantic to ORM."""
        historical_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            num_scenarios=250,
            quantile_index=12,  # Not persisted
        )

        orm_result = map_historical_var_result_to_orm(
            historical_var_result=historical_result,
            calculation_run_id=42,
            lookback_days=250,
        )

        # Verify mapped fields
        assert orm_result.fund_id == 1
        assert orm_result.confidence_level == Decimal("0.95")
        assert orm_result.horizon_days == 1
        assert orm_result.var_value_absolute == Decimal("2500.00")
        assert orm_result.var_pct_nav == Decimal("0.025")
        assert orm_result.calculation_run_id == 42
        assert orm_result.lookback_days == 250
        assert orm_result.num_observations_used == 250

    def test_map_field_name_conversions(self) -> None:
        """Verify field name conversions are correct."""
        historical_result = HistoricalVaRResult(
            fund_id=5,
            valuation_date=date(2024, 6, 15),
            confidence_level=Decimal("0.99"),
            horizon_days=1,
            var_value=Decimal("5000.00"),
            var_pct_nav=Decimal("0.05"),
            num_scenarios=500,
            quantile_index=4,
        )

        orm_result = map_historical_var_result_to_orm(
            historical_var_result=historical_result,
            calculation_run_id=100,
            lookback_days=500,
        )

        # var_value (Pydantic) → var_value_absolute (ORM)
        assert orm_result.var_value_absolute == historical_result.var_value
        # num_scenarios (Pydantic) → num_observations_used (ORM)
        assert orm_result.num_observations_used == historical_result.num_scenarios
        # quantile_index is NOT persisted
        assert not hasattr(orm_result, "quantile_index") or orm_result.quantile_index is None

    def test_map_with_zero_var_value(self) -> None:
        """Map with zero VaR value (all positive scenarios)."""
        historical_result = HistoricalVaRResult(
            fund_id=2,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("0"),
            var_pct_nav=Decimal("0"),
            num_scenarios=100,
            quantile_index=5,
        )

        orm_result = map_historical_var_result_to_orm(
            historical_var_result=historical_result,
            calculation_run_id=10,
            lookback_days=100,
        )

        assert orm_result.var_value_absolute == Decimal("0")
        assert orm_result.var_pct_nav == Decimal("0")

    def test_map_preserves_decimal_precision(self) -> None:
        """Verify Decimal precision is preserved through mapping."""
        var_value = Decimal("2345.6789")
        var_pct = Decimal("0.023456789")

        historical_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=var_value,
            var_pct_nav=var_pct,
            num_scenarios=250,
            quantile_index=12,
        )

        orm_result = map_historical_var_result_to_orm(
            historical_var_result=historical_result,
            calculation_run_id=1,
            lookback_days=250,
        )

        assert orm_result.var_value_absolute == var_value
        assert orm_result.var_pct_nav == var_pct

    def test_map_idempotent(self) -> None:
        """Mapping the same input multiple times produces identical results."""
        historical_result = HistoricalVaRResult(
            fund_id=1,
            valuation_date=date(2024, 1, 1),
            confidence_level=Decimal("0.95"),
            horizon_days=1,
            var_value=Decimal("2500.00"),
            var_pct_nav=Decimal("0.025"),
            num_scenarios=250,
            quantile_index=12,
        )

        result1 = map_historical_var_result_to_orm(historical_result, 42, 250)
        result2 = map_historical_var_result_to_orm(historical_result, 42, 250)

        assert result1.var_value_absolute == result2.var_value_absolute
        assert result1.var_pct_nav == result2.var_pct_nav
        assert result1.num_observations_used == result2.num_observations_used
