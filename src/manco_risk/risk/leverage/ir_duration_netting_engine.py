"""Interest-rate derivative duration netting engine.

Pure calculation engine for netting linear interest-rate derivatives.
Implements AIFMD Article 11 duration netting logic.
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.leverage.ir_duration_netting_models import (
    InterestRateDerivativeDirection,
    InterestRateDurationNettingInput,
    InterestRateDurationNettingResult,
    InterestRateMaturityBucket,
    InterestRateNettingBucketResult,
    LinearInterestRateDerivativeRecord,
)


class InterestRateDurationNettingEngine:
    """Calculate duration netting for linear interest-rate derivatives.

    Netting rules:
    - Records are nettable only within same currency, underlying curve, maturity bucket.
    - RECEIVE_FIXED and LONG_RATE_EXPOSURE = long side.
    - PAY_FIXED and SHORT_RATE_EXPOSURE = short side.
    - Within a nettable group:
      - gross_exposure = long_exposure + short_exposure
      - net_exposure = |long_exposure - short_exposure|
      - reduction_amount = min(long_exposure, short_exposure) * 2
    - Records with maturity before valuation date are marked non-nettable.

    Does NOT:
    - Create CommitmentReduction records.
    - Price derivatives.
    - Calculate Greeks or delta.
    - Modify AIFMD engines.
    """

    DAYS_PER_YEAR = 365

    def calculate(
        self, input: InterestRateDurationNettingInput
    ) -> InterestRateDurationNettingResult:
        """Calculate duration netting for IR derivatives.

        Parameters
        ----------
        input
            Input with valuation date and IR derivative records.

        Returns
        -------
        InterestRateDurationNettingResult
            Netting results by bucket plus aggregated totals.
        """
        valuation_date = input.valuation_date
        records = input.records

        # Separate expired from active records
        active_records = []
        expired_records = []
        warnings = []

        for record in records:
            if record.maturity_date < valuation_date:
                expired_records.append(record)
                warnings.append(
                    f"Derivative {record.derivative_id} maturity {record.maturity_date} "
                    f"is before valuation date {valuation_date}; marked non-nettable"
                )
            else:
                active_records.append(record)

        # Group active records by (currency, underlying_curve, maturity_bucket)
        bucket_key_to_records: dict[tuple, list] = {}

        for record in active_records:
            bucket = self._assign_maturity_bucket(record.maturity_date, valuation_date)
            key = (record.currency, record.underlying_curve, bucket)

            if key not in bucket_key_to_records:
                bucket_key_to_records[key] = []
            bucket_key_to_records[key].append(record)

        # Calculate netting for each bucket group
        bucket_results = []
        total_gross_exposure = Decimal("0")
        total_net_exposure = Decimal("0")
        total_reduction_amount = Decimal("0")

        for (currency, underlying_curve, bucket), group_records in bucket_key_to_records.items():
            result = self._calculate_bucket_netting(
                currency, underlying_curve, bucket, group_records
            )
            bucket_results.append(result)

            total_gross_exposure += result.long_exposure + result.short_exposure
            total_net_exposure += result.net_exposure
            total_reduction_amount += result.reduction_amount

        return InterestRateDurationNettingResult(
            valuation_date=valuation_date,
            bucket_results=bucket_results,
            total_gross_exposure=total_gross_exposure,
            total_net_exposure=total_net_exposure,
            total_reduction_amount=total_reduction_amount,
            non_nettable_records=expired_records,
            warnings=warnings,
        )

    def _assign_maturity_bucket(
        self, maturity_date: date, valuation_date: date
    ) -> InterestRateMaturityBucket:
        """Assign a maturity date to a bucket based on remaining maturity.

        Parameters
        ----------
        maturity_date
            Derivative maturity/expiry date.
        valuation_date
            Valuation date for remaining maturity calculation.

        Returns
        -------
        InterestRateMaturityBucket
            Assigned bucket.

        Uses simple day-count: remaining_days / 365 years.
        """
        if maturity_date < valuation_date:
            # Expired - should be handled by caller, but return a bucket anyway
            return InterestRateMaturityBucket.UP_TO_2Y

        remaining_days = (maturity_date - valuation_date).days
        remaining_years = Decimal(remaining_days) / Decimal(self.DAYS_PER_YEAR)

        if remaining_years <= Decimal("2"):
            return InterestRateMaturityBucket.UP_TO_2Y
        elif remaining_years <= Decimal("7"):
            return InterestRateMaturityBucket.TWO_TO_7Y
        else:
            return InterestRateMaturityBucket.OVER_7Y

    def _calculate_bucket_netting(
        self,
        currency: str,
        underlying_curve: str,
        bucket: InterestRateMaturityBucket,
        records: list[LinearInterestRateDerivativeRecord],
    ) -> InterestRateNettingBucketResult:
        """Calculate netting for a single bucket group.

        Parameters
        ----------
        currency
            Currency of the group.
        underlying_curve
            Underlying rate curve of the group.
        bucket
            Maturity bucket of the group.
        records
            All records in this group (must be non-empty).

        Returns
        -------
        InterestRateNettingBucketResult
            Netting result for the group.
        """
        long_exposure = Decimal("0")
        short_exposure = Decimal("0")

        for record in records:
            if self._is_long_side(record.direction):
                long_exposure += record.duration_equivalent_exposure_base_ccy
            else:
                short_exposure += record.duration_equivalent_exposure_base_ccy

        # Calculate net and reduction
        net_exposure = abs(long_exposure - short_exposure)
        reduction_amount = min(long_exposure, short_exposure) * Decimal("2")

        record_ids = [record.derivative_id for record in records]

        return InterestRateNettingBucketResult(
            currency=currency,
            underlying_curve=underlying_curve,
            maturity_bucket=bucket,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            net_exposure=net_exposure,
            reduction_amount=reduction_amount,
            record_ids=record_ids,
        )

    def _is_long_side(self, direction: InterestRateDerivativeDirection) -> bool:
        """Determine if direction is long (rate-increase exposure).

        Parameters
        ----------
        direction
            Interest-rate derivative direction.

        Returns
        -------
        bool
            True if long side (RECEIVE_FIXED or LONG_RATE_EXPOSURE).
        """
        return direction in (
            InterestRateDerivativeDirection.RECEIVE_FIXED,
            InterestRateDerivativeDirection.LONG_RATE_EXPOSURE,
        )
