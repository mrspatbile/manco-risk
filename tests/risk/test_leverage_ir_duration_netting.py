"""Tests for interest-rate derivative duration netting.

Validates IR duration-netting models and engine logic.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from manco_risk.risk.leverage import (
    InterestRateDerivativeDirection,
    InterestRateDurationNettingEngine,
    InterestRateDurationNettingInput,
    InterestRateMaturityBucket,
    LinearInterestRateDerivativeRecord,
)


@pytest.fixture
def valuation_date():
    """Valuation date for bucket assignments."""
    return date(2026, 6, 11)


@pytest.fixture
def sample_swap_receive_fixed_1y(valuation_date):
    """Sample receive-fixed swap, 1 year maturity."""
    return LinearInterestRateDerivativeRecord(
        derivative_id="SWAP-001",
        currency="EUR",
        underlying_curve="EURIBOR6M",
        maturity_date=valuation_date + timedelta(days=365),
        direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
        notional_base_ccy=Decimal("10000000"),
        duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        description="Receive fixed EUR swap, 1Y",
    )


@pytest.fixture
def sample_swap_pay_fixed_1y(valuation_date):
    """Sample pay-fixed swap, 1 year maturity."""
    return LinearInterestRateDerivativeRecord(
        derivative_id="SWAP-002",
        currency="EUR",
        underlying_curve="EURIBOR6M",
        maturity_date=valuation_date + timedelta(days=365),
        direction=InterestRateDerivativeDirection.PAY_FIXED,
        notional_base_ccy=Decimal("5000000"),
        duration_equivalent_exposure_base_ccy=Decimal("4500000"),
        description="Pay fixed EUR swap, 1Y",
    )


class TestLinearInterestRateDerivativeRecord:
    """Test IR derivative record model."""

    def test_valid_record(self, valuation_date):
        """Create valid IR derivative record."""
        record = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-001",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        assert record.derivative_id == "SWAP-001"
        assert record.currency == "EUR"

    def test_record_frozen(self, valuation_date):
        """Record is immutable."""
        record = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-001",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        with pytest.raises(Exception):
            record.notional_base_ccy = Decimal("11000000")

    def test_empty_derivative_id_rejected(self, valuation_date):
        """Derivative ID must be non-empty."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            LinearInterestRateDerivativeRecord(
                derivative_id="",
                currency="EUR",
                underlying_curve="EURIBOR6M",
                maturity_date=valuation_date + timedelta(days=365),
                direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
                notional_base_ccy=Decimal("10000000"),
                duration_equivalent_exposure_base_ccy=Decimal("8500000"),
            )

    def test_empty_currency_rejected(self, valuation_date):
        """Currency must be non-empty."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            LinearInterestRateDerivativeRecord(
                derivative_id="SWAP-001",
                currency="",
                underlying_curve="EURIBOR6M",
                maturity_date=valuation_date + timedelta(days=365),
                direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
                notional_base_ccy=Decimal("10000000"),
                duration_equivalent_exposure_base_ccy=Decimal("8500000"),
            )

    def test_empty_underlying_curve_rejected(self, valuation_date):
        """Underlying curve must be non-empty."""
        with pytest.raises(ValueError, match="underlying_curve must be non-empty"):
            LinearInterestRateDerivativeRecord(
                derivative_id="SWAP-001",
                currency="EUR",
                underlying_curve="",
                maturity_date=valuation_date + timedelta(days=365),
                direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
                notional_base_ccy=Decimal("10000000"),
                duration_equivalent_exposure_base_ccy=Decimal("8500000"),
            )

    def test_negative_notional_rejected(self, valuation_date):
        """Notional must be non-negative."""
        with pytest.raises(ValueError, match="notional_base_ccy must be non-negative"):
            LinearInterestRateDerivativeRecord(
                derivative_id="SWAP-001",
                currency="EUR",
                underlying_curve="EURIBOR6M",
                maturity_date=valuation_date + timedelta(days=365),
                direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
                notional_base_ccy=Decimal("-10000000"),
                duration_equivalent_exposure_base_ccy=Decimal("8500000"),
            )

    def test_negative_duration_exposure_rejected(self, valuation_date):
        """Duration exposure must be non-negative."""
        with pytest.raises(
            ValueError, match="duration_equivalent_exposure_base_ccy must be non-negative"
        ):
            LinearInterestRateDerivativeRecord(
                derivative_id="SWAP-001",
                currency="EUR",
                underlying_curve="EURIBOR6M",
                maturity_date=valuation_date + timedelta(days=365),
                direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
                notional_base_ccy=Decimal("10000000"),
                duration_equivalent_exposure_base_ccy=Decimal("-8500000"),
            )


class TestInterestRateDurationNettingInput:
    """Test netting input model."""

    def test_valid_input(self, valuation_date, sample_swap_receive_fixed_1y):
        """Create valid netting input."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y],
        )
        assert input_data.valuation_date == valuation_date
        assert len(input_data.records) == 1

    def test_empty_records_rejected(self, valuation_date):
        """Records list must be non-empty."""
        with pytest.raises(ValueError, match="records list must be non-empty"):
            InterestRateDurationNettingInput(
                valuation_date=valuation_date,
                records=[],
            )


class TestInterestRateDurationNettingEngine:
    """Test duration-netting engine."""

    def test_engine_instantiation(self):
        """Engine can be instantiated."""
        engine = InterestRateDurationNettingEngine()
        assert engine is not None

    def test_maturity_bucket_up_to_2y(self, valuation_date):
        """Maturity <= 2Y assigned to UP_TO_2Y."""
        engine = InterestRateDurationNettingEngine()
        bucket = engine._assign_maturity_bucket(
            valuation_date + timedelta(days=365), valuation_date
        )
        assert bucket == InterestRateMaturityBucket.UP_TO_2Y

    def test_maturity_bucket_exactly_2y(self, valuation_date):
        """Maturity exactly 2Y assigned to UP_TO_2Y."""
        engine = InterestRateDurationNettingEngine()
        bucket = engine._assign_maturity_bucket(
            valuation_date + timedelta(days=730), valuation_date
        )
        assert bucket == InterestRateMaturityBucket.UP_TO_2Y

    def test_maturity_bucket_2_to_7y(self, valuation_date):
        """Maturity > 2Y and <= 7Y assigned to TWO_TO_7Y."""
        engine = InterestRateDurationNettingEngine()
        bucket = engine._assign_maturity_bucket(
            valuation_date + timedelta(days=1825), valuation_date
        )
        assert bucket == InterestRateMaturityBucket.TWO_TO_7Y

    def test_maturity_bucket_exactly_7y(self, valuation_date):
        """Maturity exactly 7Y assigned to TWO_TO_7Y."""
        engine = InterestRateDurationNettingEngine()
        bucket = engine._assign_maturity_bucket(
            valuation_date + timedelta(days=2555), valuation_date
        )
        assert bucket == InterestRateMaturityBucket.TWO_TO_7Y

    def test_maturity_bucket_over_7y(self, valuation_date):
        """Maturity > 7Y assigned to OVER_7Y."""
        engine = InterestRateDurationNettingEngine()
        bucket = engine._assign_maturity_bucket(
            valuation_date + timedelta(days=2920), valuation_date
        )
        assert bucket == InterestRateMaturityBucket.OVER_7Y

    def test_same_currency_curve_bucket_opposite_directions_net(
        self, valuation_date, sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y
    ):
        """Same currency/curve/bucket opposite directions net."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # Should have one bucket result
        assert len(result.bucket_results) == 1
        bucket = result.bucket_results[0]

        # Check exposures
        assert bucket.long_exposure == Decimal("8500000")
        assert bucket.short_exposure == Decimal("4500000")
        assert bucket.net_exposure == Decimal("4000000")
        assert bucket.reduction_amount == Decimal("9000000")  # min(8.5, 4.5) * 2

    def test_same_currency_curve_bucket_same_direction_no_reduction(self, valuation_date):
        """Same direction swaps do not reduce."""
        swap1 = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-001",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        swap2 = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-002",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("5000000"),
            duration_equivalent_exposure_base_ccy=Decimal("4000000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap1, swap2],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        bucket = result.bucket_results[0]
        assert bucket.long_exposure == Decimal("12500000")
        assert bucket.short_exposure == Decimal("0")
        assert bucket.net_exposure == Decimal("12500000")
        assert bucket.reduction_amount == Decimal("0")

    def test_different_currency_does_not_net(self, valuation_date):
        """Different currencies do not net together."""
        swap_eur = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-EUR",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        swap_usd = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-USD",
            currency="USD",
            underlying_curve="SOFR",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.PAY_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap_eur, swap_usd],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # Two separate buckets
        assert len(result.bucket_results) == 2
        assert result.bucket_results[0].currency == "EUR"
        assert result.bucket_results[1].currency == "USD"

    def test_different_curve_does_not_net(self, valuation_date):
        """Different curves do not net together."""
        swap_euribor = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-EURIBOR",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        swap_eonia = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-EONIA",
            currency="EUR",
            underlying_curve="EONIA",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.PAY_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap_euribor, swap_eonia],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # Two separate buckets
        assert len(result.bucket_results) == 2
        assert result.bucket_results[0].underlying_curve == "EURIBOR6M"
        assert result.bucket_results[1].underlying_curve == "EONIA"

    def test_different_maturity_bucket_does_not_net(self, valuation_date):
        """Different maturity buckets do not net together."""
        swap_1y = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-1Y",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        swap_5y = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-5Y",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=1825),
            direction=InterestRateDerivativeDirection.PAY_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap_1y, swap_5y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # Two separate buckets
        assert len(result.bucket_results) == 2
        assert result.bucket_results[0].maturity_bucket == InterestRateMaturityBucket.UP_TO_2Y
        assert result.bucket_results[1].maturity_bucket == InterestRateMaturityBucket.TWO_TO_7Y

    def test_total_gross_exposure_calculation(
        self, valuation_date, sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y
    ):
        """Total gross exposure is sum of all exposures."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        expected_gross = Decimal("8500000") + Decimal("4500000")
        assert result.total_gross_exposure == expected_gross

    def test_total_net_exposure_calculation(
        self, valuation_date, sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y
    ):
        """Total net exposure is sum of net exposures."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # Net = |8500000 - 4500000| = 4000000
        assert result.total_net_exposure == Decimal("4000000")

    def test_total_reduction_amount_calculation(
        self, valuation_date, sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y
    ):
        """Total reduction amount equals gross minus net."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        expected_reduction = result.total_gross_exposure - result.total_net_exposure
        assert result.total_reduction_amount == expected_reduction

    def test_expired_maturity_marked_non_nettable(self, valuation_date):
        """Derivatives with maturity before valuation date marked non-nettable."""
        swap_expired = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-EXPIRED",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date - timedelta(days=1),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        swap_active = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-ACTIVE",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.RECEIVE_FIXED,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap_expired, swap_active],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        # One bucket for active, one non-nettable record
        assert len(result.bucket_results) == 1
        assert len(result.non_nettable_records) == 1
        assert result.non_nettable_records[0].derivative_id == "SWAP-EXPIRED"
        assert len(result.warnings) >= 1

    def test_bucket_result_record_ids_populated(
        self, valuation_date, sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y
    ):
        """Bucket result includes all record IDs in the group."""
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[sample_swap_receive_fixed_1y, sample_swap_pay_fixed_1y],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        bucket = result.bucket_results[0]
        assert "SWAP-001" in bucket.record_ids
        assert "SWAP-002" in bucket.record_ids
        assert len(bucket.record_ids) == 2

    def test_long_rate_exposure_treated_as_long(self, valuation_date):
        """LONG_RATE_EXPOSURE direction treated as long side."""
        swap = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-LONG",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.LONG_RATE_EXPOSURE,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        bucket = result.bucket_results[0]
        assert bucket.long_exposure == Decimal("8500000")
        assert bucket.short_exposure == Decimal("0")

    def test_short_rate_exposure_treated_as_short(self, valuation_date):
        """SHORT_RATE_EXPOSURE direction treated as short side."""
        swap = LinearInterestRateDerivativeRecord(
            derivative_id="SWAP-SHORT",
            currency="EUR",
            underlying_curve="EURIBOR6M",
            maturity_date=valuation_date + timedelta(days=365),
            direction=InterestRateDerivativeDirection.SHORT_RATE_EXPOSURE,
            notional_base_ccy=Decimal("10000000"),
            duration_equivalent_exposure_base_ccy=Decimal("8500000"),
        )
        input_data = InterestRateDurationNettingInput(
            valuation_date=valuation_date,
            records=[swap],
        )

        engine = InterestRateDurationNettingEngine()
        result = engine.calculate(input_data)

        bucket = result.bucket_results[0]
        assert bucket.long_exposure == Decimal("0")
        assert bucket.short_exposure == Decimal("8500000")

    def test_no_quantlib_imports(self):
        """Engine has no QuantLib imports."""
        import inspect

        import manco_risk.risk.leverage.ir_duration_netting_engine as module

        source = inspect.getsource(module)
        assert "quantlib" not in source.lower()
        assert "ql." not in source.lower()

    def test_no_database_imports(self):
        """Engine has no database imports."""
        import inspect

        import manco_risk.risk.leverage.ir_duration_netting_engine as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
