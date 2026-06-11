"""Tests for leverage limit monitoring.

Validates limit definitions, monitoring logic, and result generation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.limits import (
    LeverageLimitMonitoringEngine,
    LimitCheckResult,
    LimitDefinition,
    LimitDirection,
    LimitMetric,
    LimitSource,
    LimitStatus,
    LimitType,
    MetricObservation,
)


@pytest.fixture
def sample_limit_aifmd_gross_hard():
    """AIFMD gross leverage hard limit."""
    return LimitDefinition(
        limit_id="AIFMD-GROSS-HARD",
        metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
        source=LimitSource.REGULATORY,
        limit_type=LimitType.HARD_LIMIT,
        direction=LimitDirection.MAXIMUM,
        threshold=Decimal("6.0"),
        description="AIFMD gross leverage regulatory limit",
    )


@pytest.fixture
def sample_observation_aifmd_gross():
    """AIFMD gross leverage observation."""
    return MetricObservation(
        metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
        value=Decimal("3.50"),
        fund_id=1,
        valuation_date=date(2026, 6, 11),
    )


class TestLimitDefinition:
    """Test limit definition model."""

    def test_valid_limit_definition(self):
        """Create valid limit definition."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
        )
        assert limit.limit_id == "TEST-001"
        assert limit.is_active is True

    def test_limit_definition_frozen(self):
        """Limit definition is immutable."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
        )
        with pytest.raises(Exception):
            limit.threshold = Decimal("3.00")

    def test_limit_definition_rejects_empty_limit_id(self):
        """Limit ID must be non-empty."""
        with pytest.raises(ValueError, match="limit_id must be non-empty"):
            LimitDefinition(
                limit_id="",
                metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
                source=LimitSource.REGULATORY,
                limit_type=LimitType.HARD_LIMIT,
                direction=LimitDirection.MAXIMUM,
                threshold=Decimal("2.50"),
            )

    def test_limit_definition_rejects_negative_threshold(self):
        """Threshold must be non-negative."""
        with pytest.raises(ValueError, match="threshold must be non-negative"):
            LimitDefinition(
                limit_id="TEST-001",
                metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
                source=LimitSource.REGULATORY,
                limit_type=LimitType.HARD_LIMIT,
                direction=LimitDirection.MAXIMUM,
                threshold=Decimal("-1.00"),
            )

    def test_limit_definition_zero_threshold_valid(self):
        """Zero threshold is valid."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("0"),
        )
        assert limit.threshold == Decimal("0")

    def test_limit_definition_with_description(self):
        """Limit definition can have optional description."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
            description="AIFMD Article 25 gross leverage cap",
        )
        assert limit.description == "AIFMD Article 25 gross leverage cap"

    def test_limit_definition_rejects_empty_description(self):
        """Description, if provided, must be non-empty."""
        with pytest.raises(ValueError, match="description must be non-empty"):
            LimitDefinition(
                limit_id="TEST-001",
                metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
                source=LimitSource.REGULATORY,
                limit_type=LimitType.HARD_LIMIT,
                direction=LimitDirection.MAXIMUM,
                threshold=Decimal("2.50"),
                description="",
            )

    def test_limit_definition_is_active_flag(self):
        """Can create inactive limits."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
            is_active=False,
        )
        assert limit.is_active is False


class TestMetricObservation:
    """Test metric observation model."""

    def test_valid_observation(self):
        """Create valid metric observation."""
        obs = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.30"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        assert obs.value == Decimal("2.30")
        assert obs.fund_id == 1

    def test_observation_frozen(self):
        """Observation is immutable."""
        obs = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.30"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        with pytest.raises(Exception):
            obs.value = Decimal("2.40")

    def test_observation_rejects_negative_value(self):
        """Observation value must be non-negative."""
        with pytest.raises(ValueError, match="value must be non-negative"):
            MetricObservation(
                metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
                value=Decimal("-1.00"),
                fund_id=1,
                valuation_date=date(2026, 6, 11),
            )

    def test_observation_zero_value_valid(self):
        """Zero observation value is valid."""
        obs = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("0"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        assert obs.value == Decimal("0")

    def test_observation_with_source_reference(self):
        """Observation can have source reference."""
        obs = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.30"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
            source_reference="calc-run-123",
        )
        assert obs.source_reference == "calc-run-123"


class TestLimitCheckResult:
    """Test limit check result model."""

    def test_valid_result(self, sample_limit_aifmd_gross_hard, sample_observation_aifmd_gross):
        """Create valid limit check result."""
        result = LimitCheckResult(
            limit=sample_limit_aifmd_gross_hard,
            observation=sample_observation_aifmd_gross,
            status=LimitStatus.WITHIN_LIMIT,
            excess_amount=Decimal("0"),
            excess_ratio=None,
            message="Within limit",
        )
        assert result.status == LimitStatus.WITHIN_LIMIT

    def test_result_frozen(self, sample_limit_aifmd_gross_hard, sample_observation_aifmd_gross):
        """Result is immutable."""
        result = LimitCheckResult(
            limit=sample_limit_aifmd_gross_hard,
            observation=sample_observation_aifmd_gross,
            status=LimitStatus.WITHIN_LIMIT,
            excess_amount=Decimal("0"),
            excess_ratio=None,
            message="Within limit",
        )
        with pytest.raises(Exception):
            result.status = LimitStatus.BREACH

    def test_result_rejects_negative_excess(self, sample_limit_aifmd_gross_hard):
        """Excess amount must be non-negative."""
        with pytest.raises(ValueError, match="excess_amount must be non-negative"):
            LimitCheckResult(
                limit=sample_limit_aifmd_gross_hard,
                observation=None,
                status=LimitStatus.NOT_ASSESSED,
                excess_amount=Decimal("-1.00"),
                excess_ratio=None,
                message="Test",
            )

    def test_result_rejects_empty_message(self, sample_limit_aifmd_gross_hard):
        """Message must be non-empty."""
        with pytest.raises(ValueError, match="message must be non-empty"):
            LimitCheckResult(
                limit=sample_limit_aifmd_gross_hard,
                observation=None,
                status=LimitStatus.NOT_ASSESSED,
                excess_amount=Decimal("0"),
                excess_ratio=None,
                message="",
            )


class TestLeverageLimitMonitoringEngine:
    """Test limit monitoring engine."""

    def test_engine_instantiation(self):
        """Engine can be instantiated."""
        engine = LeverageLimitMonitoringEngine()
        assert engine is not None

    def test_maximum_limit_within_threshold(self):
        """Maximum limit within threshold gives WITHIN_LIMIT."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert len(result.results) == 1
        assert result.results[0].status == LimitStatus.WITHIN_LIMIT
        assert result.results[0].excess_amount == Decimal("0")

    def test_maximum_limit_at_threshold(self):
        """Maximum limit exactly at threshold gives WITHIN_LIMIT."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("3.00"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.WITHIN_LIMIT

    def test_maximum_hard_limit_breach(self):
        """Maximum hard limit breach gives BREACH."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("3.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.BREACH
        assert result.results[0].excess_amount == Decimal("0.50")

    def test_maximum_warning_threshold(self):
        """Maximum warning threshold gives WARNING."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.INTERNAL,
            limit_type=LimitType.WARNING_THRESHOLD,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.80"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.WARNING
        assert result.results[0].excess_amount == Decimal("0.30")

    def test_maximum_escalation_threshold(self):
        """Maximum escalation threshold gives WARNING."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.FUND_DOCUMENT,
            limit_type=LimitType.ESCALATION_THRESHOLD,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.40"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.WARNING

    def test_minimum_limit_within_threshold(self):
        """Minimum limit within threshold gives WITHIN_LIMIT."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.DIRECT_BORROWING,
            source=LimitSource.FUND_DOCUMENT,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MINIMUM,
            threshold=Decimal("0.50"),
        )
        observation = MetricObservation(
            metric=LimitMetric.DIRECT_BORROWING,
            value=Decimal("0.75"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.WITHIN_LIMIT

    def test_minimum_hard_limit_breach(self):
        """Minimum hard limit breach gives BREACH."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.DIRECT_BORROWING,
            source=LimitSource.FUND_DOCUMENT,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MINIMUM,
            threshold=Decimal("0.50"),
        )
        observation = MetricObservation(
            metric=LimitMetric.DIRECT_BORROWING,
            value=Decimal("0.30"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].status == LimitStatus.BREACH
        assert result.results[0].excess_amount == Decimal("0.20")

    def test_excess_amount_calculated_correctly(self):
        """Excess amount calculation is correct."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.35"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].excess_amount == Decimal("0.35")

    def test_excess_ratio_calculated_correctly(self):
        """Excess ratio calculation is correct."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.40"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        # excess_ratio = 0.40 / 2.00 = 0.20
        assert result.results[0].excess_ratio == Decimal("0.20")

    def test_zero_threshold_no_divide_by_zero(self):
        """Zero threshold does not cause division by zero."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("0"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("0.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert result.results[0].excess_ratio is None

    def test_inactive_limits_ignored(self):
        """Inactive limits are not checked."""
        active_limit = LimitDefinition(
            limit_id="ACTIVE-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        inactive_limit = LimitDefinition(
            limit_id="INACTIVE-001",
            metric=LimitMetric.AIFMD_COMMITMENT_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("1.50"),
            is_active=False,
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("1.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([active_limit, inactive_limit], [observation])

        # Only one result (active limit)
        assert len(result.results) == 1
        assert result.results[0].limit.limit_id == "ACTIVE-001"

    def test_missing_observation_raises_error(self):
        """Empty observations list raises ValueError."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )

        engine = LeverageLimitMonitoringEngine()
        with pytest.raises(ValueError, match="observations must contain at least one"):
            engine.check_limits([limit], [])

    def test_missing_observation_for_specific_metric(self):
        """Missing observation for a metric gives NOT_ASSESSED."""
        limit_gross = LimitDefinition(
            limit_id="GROSS-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        limit_commitment = LimitDefinition(
            limit_id="COMMITMENT-001",
            metric=LimitMetric.AIFMD_COMMITMENT_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("1.50"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("1.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit_gross, limit_commitment], [observation])

        # Gross limit is checked, commitment is NOT_ASSESSED
        assert result.results[0].status == LimitStatus.WITHIN_LIMIT
        assert result.results[1].status == LimitStatus.NOT_ASSESSED
        assert result.results[1].observation is None

    def test_multiple_limits_for_same_metric(self):
        """Multiple limits for same metric are all checked."""
        limit_hard = LimitDefinition(
            limit_id="HARD-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
        )
        limit_warning = LimitDefinition(
            limit_id="WARNING-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.INTERNAL,
            limit_type=LimitType.WARNING_THRESHOLD,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.75"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit_hard, limit_warning], [observation])

        # Hard limit OK, warning threshold breached
        assert len(result.results) == 2
        assert result.results[0].status == LimitStatus.WITHIN_LIMIT
        assert result.results[1].status == LimitStatus.WARNING

    def test_multiple_observations_different_metrics(self):
        """Multiple observations for different metrics matched correctly."""
        limit_gross = LimitDefinition(
            limit_id="GROSS-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
        )
        limit_ucits = LimitDefinition(
            limit_id="UCITS-001",
            metric=LimitMetric.UCITS_GLOBAL_EXPOSURE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("1.00"),
        )
        obs_gross = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("2.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        obs_ucits = MetricObservation(
            metric=LimitMetric.UCITS_GLOBAL_EXPOSURE,
            value=Decimal("0.85"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit_gross, limit_ucits], [obs_gross, obs_ucits])

        assert len(result.results) == 2
        assert result.results[0].observation.metric == LimitMetric.AIFMD_GROSS_LEVERAGE
        assert result.results[1].observation.metric == LimitMetric.UCITS_GLOBAL_EXPOSURE

    def test_multiple_fund_ids_raises_error(self):
        """Multiple fund IDs in observations raises ValueError."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        obs1 = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("1.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        obs2 = MetricObservation(
            metric=LimitMetric.AIFMD_COMMITMENT_LEVERAGE,
            value=Decimal("1.20"),
            fund_id=2,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()

        with pytest.raises(ValueError, match="observations must have consistent fund_id"):
            engine.check_limits([limit], [obs1, obs2])

    def test_multiple_valuation_dates_raises_error(self):
        """Multiple valuation dates in observations raises ValueError."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
        )
        obs1 = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("1.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )
        obs2 = MetricObservation(
            metric=LimitMetric.AIFMD_COMMITMENT_LEVERAGE,
            value=Decimal("1.20"),
            fund_id=1,
            valuation_date=date(2026, 6, 10),
        )

        engine = LeverageLimitMonitoringEngine()

        with pytest.raises(ValueError, match="observations must have consistent valuation_date"):
            engine.check_limits([limit], [obs1, obs2])

    def test_no_active_limits_returns_empty_results(self):
        """No active limits returns empty results."""
        limit = LimitDefinition(
            limit_id="TEST-001",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.00"),
            is_active=False,
        )
        observation = MetricObservation(
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            value=Decimal("1.50"),
            fund_id=1,
            valuation_date=date(2026, 6, 11),
        )

        engine = LeverageLimitMonitoringEngine()
        result = engine.check_limits([limit], [observation])

        assert len(result.results) == 0

    def test_loan_originating_aif_175_limit(self):
        """Loan-originating AIF 175% limit can be represented."""
        limit = LimitDefinition(
            limit_id="LOAN-ORIG-175",
            metric=LimitMetric.LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("1.75"),
            description="Loan-originating AIF Article 16 max 175% commitment",
        )
        assert limit.threshold == Decimal("1.75")
        assert limit.metric == LimitMetric.LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE

    def test_loan_originating_aif_300_limit(self):
        """Loan-originating AIF 300% limit can be represented."""
        limit = LimitDefinition(
            limit_id="LOAN-ORIG-300",
            metric=LimitMetric.LOAN_ORIGINATING_AIF_COMMITMENT_LEVERAGE,
            source=LimitSource.REGULATORY,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("3.00"),
            description="Loan-originating AIF Article 16 max 300% commitment",
        )
        assert limit.threshold == Decimal("3.00")

    def test_fund_document_leverage_limit(self):
        """Fund-document leverage limit can be represented."""
        limit = LimitDefinition(
            limit_id="FUND-COMMITMENT-CAP",
            metric=LimitMetric.AIFMD_COMMITMENT_LEVERAGE,
            source=LimitSource.FUND_DOCUMENT,
            limit_type=LimitType.HARD_LIMIT,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("2.50"),
            description="Fund prospectus commitment leverage cap",
        )
        assert limit.source == LimitSource.FUND_DOCUMENT

    def test_internal_warning_threshold(self):
        """Internal warning threshold can be represented."""
        limit = LimitDefinition(
            limit_id="INTERNAL-WARN",
            metric=LimitMetric.AIFMD_GROSS_LEVERAGE,
            source=LimitSource.INTERNAL,
            limit_type=LimitType.WARNING_THRESHOLD,
            direction=LimitDirection.MAXIMUM,
            threshold=Decimal("1.80"),
            description="Internal risk monitoring threshold",
        )
        assert limit.source == LimitSource.INTERNAL
        assert limit.limit_type == LimitType.WARNING_THRESHOLD

    def test_no_database_imports(self):
        """Monitoring module has no database imports."""
        import inspect

        import manco_risk.risk.limits.leverage_limit_engine as module

        source = inspect.getsource(module)
        assert "from manco_risk.database" not in source
        assert "import.*repository" not in source.lower()
