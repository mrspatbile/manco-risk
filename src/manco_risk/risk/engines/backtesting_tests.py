"""Statistical tests for VaR backtesting.

Implements Kupiec unconditional coverage test (POF) and
placeholder for Christoffersen test (deferred).

Phase 1: Kupiec only. Christoffersen deferred to Phase 2.
"""

import math
from decimal import Decimal

from scipy.stats import chi2  # type: ignore[import-untyped]

from manco_risk.risk.models.kupiec_test import KupiecTestResult


class KupiecTest:
    """Kupiec POF (Proportion of Failures) unconditional coverage test.

    Tests whether the observed number of VaR breaches is consistent
    with the expected breach probability under a binomial model.

    The test statistic follows a chi-square distribution with 1 degree of freedom
    under the null hypothesis.

    Example:
        >>> result = KupiecTest.calculate(
        ...     num_observations=250,
        ...     num_breaches=8,
        ...     expected_breach_probability=Decimal("0.05"),
        ... )
        >>> print(result.reject_null)  # True if test rejects at alpha=0.05
    """

    @staticmethod
    def calculate(
        num_observations: int,
        num_breaches: int,
        expected_breach_probability: Decimal,
        alpha: Decimal = Decimal("0.05"),
    ) -> KupiecTestResult:
        """Calculate Kupiec POF test result.

        Parameters
        ----------
        num_observations : int
            Number of valid aligned VaR/P&L observations.
        num_breaches : int
            Observed number of VaR breaches.
        expected_breach_probability : Decimal
            Expected breach probability (e.g., 0.05 for 95% VaR).
        alpha : Decimal, optional
            Significance level for hypothesis test (default 0.05).

        Returns
        -------
        KupiecTestResult
            Test statistic, p-value, and rejection decision.

        Raises
        ------
        ValueError
            If inputs are invalid (delegated to KupiecTestResult validation).

        Notes
        -----
        Likelihood-ratio statistic under null and alternative:
        - Under H₀: breach probability = expected_breach_probability
        - Under H₁: breach probability = num_breaches / num_observations
        - LR = 2 * (ln L₁ - ln L₀)
        - Under H₀, LR ~ χ²(1)

        Boundary cases:
        - 0 * log(0) is treated as 0 by convention
        - If num_breaches = 0, all terms with log(num_breaches) are omitted
        - If num_breaches = num_observations, all terms with log(num_non_breaches) are omitted
        """
        # Calculate observed breach probability
        observed_prob = Decimal(num_breaches) / Decimal(num_observations)

        # Calculate likelihood-ratio statistic
        lr_statistic = KupiecTest._calculate_lr_statistic(
            num_observations, num_breaches, expected_breach_probability
        )

        # Calculate p-value from chi-square distribution (df=1)
        # SciPy chi2.sf() is survival function (1 - CDF) = P(X > x)
        p_value_float = float(chi2.sf(float(lr_statistic), df=1))
        p_value = Decimal(str(p_value_float))

        # Determine rejection
        reject_null = p_value < alpha

        # Create result
        result = KupiecTestResult(
            num_observations=num_observations,
            num_breaches=num_breaches,
            expected_breach_probability=expected_breach_probability,
            observed_breach_probability=observed_prob,
            lr_statistic=lr_statistic,
            p_value=p_value,
            alpha=alpha,
            reject_null=reject_null,
        )

        return result

    @staticmethod
    def _calculate_lr_statistic(
        n: int,
        x: int,
        p: Decimal,
    ) -> Decimal:
        """Calculate likelihood-ratio statistic for Kupiec POF test.

        Under the null hypothesis:
        LR_uc = 2 * [x*ln(x/n) + (n-x)*ln((n-x)/n) - x*ln(p) - (n-x)*ln(1-p)]

        Boundary cases:
        - 0 * ln(0) = 0 by convention
        - If x = 0, omit first and third terms
        - If x = n, omit second and fourth terms

        Parameters
        ----------
        n : int
            Number of observations.
        x : int
            Number of breaches.
        p : Decimal
            Expected breach probability.

        Returns
        -------
        Decimal
            Likelihood-ratio test statistic.
        """
        p_float = float(p)
        p_one_minus = float(Decimal("1") - p)

        # Term 1: x * ln(x/n), omitted if x = 0
        term1 = 0.0
        if x > 0:
            term1 = x * math.log(x / n)

        # Term 2: (n-x) * ln((n-x)/n), omitted if x = n
        term2 = 0.0
        if x < n:
            n_minus_x = n - x
            term2 = n_minus_x * math.log(n_minus_x / n)

        # Term 3: -x * ln(p), omitted if x = 0
        term3 = 0.0
        if x > 0:
            term3 = -x * math.log(p_float)

        # Term 4: -(n-x) * ln(1-p), omitted if x = n
        term4 = 0.0
        if x < n:
            n_minus_x = n - x
            term4 = -n_minus_x * math.log(p_one_minus)

        # Combine terms and multiply by 2
        lr = 2.0 * (term1 + term2 + term3 + term4)

        # Clamp to zero to handle floating-point precision issues
        # (when observed equals expected, should be exactly zero but may be slightly negative)
        if lr < 0 and lr > -1e-10:
            lr = 0.0

        return Decimal(str(lr))
