"""Leverage limit monitoring engine.

Pure calculation engine for checking metric observations against limit definitions.
Does not calculate leverage or persist results.
"""

from decimal import Decimal

from manco_risk.risk.limits.leverage_limit_models import (
    LeverageLimitMonitoringResult,
    LimitCheckResult,
    LimitDefinition,
    LimitDirection,
    LimitStatus,
    LimitType,
    MetricObservation,
)


class LeverageLimitMonitoringEngine:
    """Check metric observations against leverage limit definitions.

    Responsibilities:
    - Match observations to limits by metric.
    - Apply direction (MAXIMUM vs MINIMUM) logic.
    - Determine status (WITHIN_LIMIT, WARNING, BREACH, NOT_ASSESSED).
    - Calculate excess amount and ratio.
    - Track processing warnings.

    Does NOT:
    - Calculate leverage or exposure.
    - Persist limits or results.
    - Generate reports.
    - Make fund compliance decisions (that's governance).
    """

    def check_limits(
        self,
        limits: list[LimitDefinition],
        observations: list[MetricObservation],
    ) -> LeverageLimitMonitoringResult:
        """Check metric observations against limit definitions.

        Parameters
        ----------
        limits
            List of limit definitions to check.
        observations
            List of metric observations to check against limits.

        Returns
        -------
        LeverageLimitMonitoringResult
            Results of checking all active limits.

        Raises
        ------
        ValueError
            If observations contain inconsistent fund_id or valuation_date.
        """
        # Validate observation consistency
        fund_ids = {obs.fund_id for obs in observations}
        valuation_dates = {obs.valuation_date for obs in observations}

        if len(fund_ids) > 1:
            raise ValueError(f"observations must have consistent fund_id, got {fund_ids}")
        if len(valuation_dates) > 1:
            raise ValueError(
                f"observations must have consistent valuation_date, got {valuation_dates}"
            )

        # Get fund_id and valuation_date from observations if available
        fund_id = observations[0].fund_id if observations else 1
        valuation_date = observations[0].valuation_date if observations else None

        if valuation_date is None:
            raise ValueError("observations must contain at least one observation")

        # Filter active limits
        active_limits = [lim for lim in limits if lim.is_active]

        # Build observation map by metric
        obs_by_metric = {obs.metric: obs for obs in observations}

        # Check each limit
        results: list[LimitCheckResult] = []
        warnings: list[str] = []

        for limit in active_limits:
            observation = obs_by_metric.get(limit.metric)
            result = self._check_limit(limit, observation)
            results.append(result)

        return LeverageLimitMonitoringResult(
            fund_id=fund_id,
            valuation_date=valuation_date,
            results=results,
            warnings=warnings,
        )

    def _check_limit(
        self, limit: LimitDefinition, observation: MetricObservation | None
    ) -> LimitCheckResult:
        """Check a single observation against a limit definition.

        Parameters
        ----------
        limit
            Limit definition.
        observation
            Metric observation (may be None).

        Returns
        -------
        LimitCheckResult
            Result of the check.
        """
        # No observation available
        if observation is None:
            return LimitCheckResult(
                limit=limit,
                observation=None,
                status=LimitStatus.NOT_ASSESSED,
                excess_amount=Decimal("0"),
                excess_ratio=None,
                message=f"No observation available for metric {limit.metric.value}",
            )

        # Apply direction-specific logic
        if limit.direction == LimitDirection.MAXIMUM:
            return self._check_maximum(limit, observation)
        else:  # MINIMUM
            return self._check_minimum(limit, observation)

    def _check_maximum(
        self, limit: LimitDefinition, observation: MetricObservation
    ) -> LimitCheckResult:
        """Check observation against MAXIMUM limit (value <= threshold).

        Parameters
        ----------
        limit
            Limit definition with MAXIMUM direction.
        observation
            Metric observation.

        Returns
        -------
        LimitCheckResult
            Result with appropriate status and excess calculations.
        """
        if observation.value <= limit.threshold:
            return LimitCheckResult(
                limit=limit,
                observation=observation,
                status=LimitStatus.WITHIN_LIMIT,
                excess_amount=Decimal("0"),
                excess_ratio=None,
                message=f"{limit.metric.value} {observation.value} within limit {limit.threshold}",
            )

        # Value exceeds threshold
        excess_amount = observation.value - limit.threshold
        excess_ratio = excess_amount / limit.threshold if limit.threshold > Decimal("0") else None

        # Determine status based on limit type
        if limit.limit_type == LimitType.HARD_LIMIT:
            status = LimitStatus.BREACH
        else:  # WARNING_THRESHOLD or ESCALATION_THRESHOLD
            status = LimitStatus.WARNING

        message = (
            f"{limit.metric.value} {observation.value} exceeds "
            f"{limit.limit_type.value} {limit.threshold} by {excess_amount}"
        )

        return LimitCheckResult(
            limit=limit,
            observation=observation,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
            message=message,
        )

    def _check_minimum(
        self, limit: LimitDefinition, observation: MetricObservation
    ) -> LimitCheckResult:
        """Check observation against MINIMUM limit (value >= threshold).

        Parameters
        ----------
        limit
            Limit definition with MINIMUM direction.
        observation
            Metric observation.

        Returns
        -------
        LimitCheckResult
            Result with appropriate status and excess calculations.
        """
        if observation.value >= limit.threshold:
            return LimitCheckResult(
                limit=limit,
                observation=observation,
                status=LimitStatus.WITHIN_LIMIT,
                excess_amount=Decimal("0"),
                excess_ratio=None,
                message=f"{limit.metric.value} {observation.value} meets minimum {limit.threshold}",
            )

        # Value below threshold
        excess_amount = limit.threshold - observation.value
        excess_ratio = excess_amount / limit.threshold if limit.threshold > Decimal("0") else None

        # Determine status based on limit type
        if limit.limit_type == LimitType.HARD_LIMIT:
            status = LimitStatus.BREACH
        else:  # WARNING_THRESHOLD or ESCALATION_THRESHOLD
            status = LimitStatus.WARNING

        message = (
            f"{limit.metric.value} {observation.value} below "
            f"{limit.limit_type.value} {limit.threshold} by {excess_amount}"
        )

        return LimitCheckResult(
            limit=limit,
            observation=observation,
            status=status,
            excess_amount=excess_amount,
            excess_ratio=excess_ratio,
            message=message,
        )
