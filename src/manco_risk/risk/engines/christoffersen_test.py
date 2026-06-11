"""Christoffersen conditional coverage test for VaR backtesting.

Implements the Christoffersen test combining unconditional coverage (UC)
and independence (Ind) for breach sequence analysis.

Phase 1: Full Christoffersen implementation with UC and Ind tests.
Conditional coverage (CC) is the combined test.
"""

import math
from decimal import Decimal

from scipy.stats import chi2  # type: ignore[import-untyped]

from manco_risk.risk.models.backtest_observation_index import get_breach_sequence
from manco_risk.risk.models.backtest_result import BacktestResult
from manco_risk.risk.models.christoffersen_test import (
    ChristoffersenTestResult,
    TransitionMatrix,
)


class ChristoffersenTest:
    """Christoffersen conditional coverage test for VaR backtesting.

    Tests whether VaR breaches are (1) correctly calibrated in frequency
    and (2) independent (not clustered).

    Components:
    - UC test: unconditional coverage (breach probability)
    - Ind test: independence (no clustering of breaches)
    - CC test: conditional coverage (joint UC + Ind)

    Example:
        >>> result = ChristoffersenTest.calculate(backtest_result)
        >>> print(f"Breaches clustered: {result.reject_ind}")
        >>> print(f"Overall test failed: {result.reject_cc}")
    """

    @staticmethod
    def calculate(
        backtest_result: BacktestResult,
        alpha: Decimal = Decimal("0.05"),
    ) -> ChristoffersenTestResult:
        """Calculate Christoffersen conditional coverage test.

        Parameters
        ----------
        backtest_result : BacktestResult
            Backtesting counts and aligned observations.
        alpha : Decimal, optional
            Significance level for hypothesis tests (default 0.05).

        Returns
        -------
        ChristoffersenTestResult
            UC, Ind, and CC test statistics, p-values, and rejections.

        Raises
        ------
        ValueError
            If aligned observations < 2 (cannot compute transitions).
        """
        num_observations = backtest_result.num_valid_aligned
        num_breaches = backtest_result.num_breaches
        expected_prob = backtest_result.expected_breach_probability
        aligned_obs = backtest_result.aligned_observations

        # Extract breach sequence
        breach_sequence = get_breach_sequence(aligned_obs)

        # Calculate transition counts
        transition_matrix = ChristoffersenTest._calculate_transitions(breach_sequence)

        # UC test: same as Kupiec
        uc_stat = ChristoffersenTest._calculate_uc_statistic(
            num_observations, num_breaches, expected_prob
        )
        uc_p_value = Decimal(str(float(chi2.sf(float(uc_stat), df=1))))

        # Independence test
        ind_stat = ChristoffersenTest._calculate_independence_statistic(transition_matrix)
        ind_p_value = Decimal(str(float(chi2.sf(float(ind_stat), df=1))))

        # Conditional coverage: UC + Ind
        cc_stat = uc_stat + ind_stat
        cc_p_value = Decimal(str(float(chi2.sf(float(cc_stat), df=2))))

        # Determine rejections
        reject_uc = uc_p_value < alpha
        reject_ind = ind_p_value < alpha
        reject_cc = cc_p_value < alpha

        result = ChristoffersenTestResult(
            num_observations=num_observations,
            num_breaches=num_breaches,
            expected_breach_probability=expected_prob,
            transition_matrix=transition_matrix,
            uc_test_statistic=uc_stat,
            uc_p_value=uc_p_value,
            ind_test_statistic=ind_stat,
            ind_p_value=ind_p_value,
            cc_test_statistic=cc_stat,
            cc_p_value=cc_p_value,
            alpha=alpha,
            reject_uc=reject_uc,
            reject_ind=reject_ind,
            reject_cc=reject_cc,
        )

        return result

    @staticmethod
    def _calculate_transitions(breach_sequence: list[bool]) -> TransitionMatrix:
        """Calculate transition matrix from breach sequence.

        State transitions for consecutive observations:
        - n00: non-breach → non-breach
        - n01: non-breach → breach
        - n10: breach → non-breach
        - n11: breach → breach

        Parameters
        ----------
        breach_sequence : list[bool]
            Sequence of breach indicators (True = breach).

        Returns
        -------
        TransitionMatrix
            Transition counts.
        """
        n00 = n01 = n10 = n11 = 0

        for i in range(len(breach_sequence) - 1):
            current = breach_sequence[i]
            next_state = breach_sequence[i + 1]

            if not current and not next_state:
                n00 += 1
            elif not current and next_state:
                n01 += 1
            elif current and not next_state:
                n10 += 1
            elif current and next_state:
                n11 += 1

        return TransitionMatrix(n00=n00, n01=n01, n10=n10, n11=n11)

    @staticmethod
    def _calculate_uc_statistic(
        n: int,
        x: int,
        p: Decimal,
    ) -> Decimal:
        """Calculate UC (unconditional coverage) test statistic.

        Same as Kupiec POF test:
        LR_uc = 2 * [x*ln(x/n) + (n-x)*ln((n-x)/n) - x*ln(p) - (n-x)*ln(1-p)]

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
            UC test statistic.
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

        lr = 2.0 * (term1 + term2 + term3 + term4)

        # Clamp small negative values to zero (floating-point precision)
        if lr < 0 and lr > -1e-10:
            lr = 0.0

        return Decimal(str(lr))

    @staticmethod
    def _calculate_independence_statistic(tm: TransitionMatrix) -> Decimal:
        """Calculate independence test statistic from transition matrix.

        Tests whether breach probabilities differ conditional on previous state:
        - H₀: P(breach | no breach) = P(breach | breach)
        - H₁: Probabilities differ (clustering)

        LR_ind = 2 * [n01*ln(π01) + n11*ln(π11) + n00*ln(1-π01) + n10*ln(1-π11)
                      - (n01+n11)*ln(π) - (n00+n10)*ln(1-π)]

        where:
        - π01 = n01 / (n00 + n01) = P(breach | no breach)
        - π11 = n11 / (n10 + n11) = P(breach | breach)
        - π = (n01 + n11) / (n00 + n01 + n10 + n11) = overall breach prob

        Handle edge cases:
        - If n0 = 0, skip terms involving n00, n01
        - If n1 = 0, skip terms involving n10, n11
        - If π01 = 0 or 1, handle log terms carefully
        - If π11 = 0 or 1, handle log terms carefully

        Parameters
        ----------
        tm : TransitionMatrix
            Transition counts.

        Returns
        -------
        Decimal
            Independence test statistic.
        """
        n00, n01, n10, n11 = tm.n00, tm.n01, tm.n10, tm.n11
        n0 = n00 + n01
        n1 = n10 + n11
        total = n00 + n01 + n10 + n11

        # Handle edge case: no transitions
        if total < 2:
            return Decimal("0")

        # Overall breach probability
        n_breach = n01 + n11
        pi = n_breach / total if total > 0 else 0.0

        # Conditional probabilities
        pi01 = n01 / n0 if n0 > 0 else 0.0
        pi11 = n11 / n1 if n1 > 0 else 0.0

        # Calculate terms carefully, omitting 0*log(0) = 0
        lr_terms = 0.0

        # Conditional state 0 terms: n00*ln(1-π01) + n01*ln(π01)
        if n0 > 0:
            if n01 > 0 and pi01 > 0:
                lr_terms += n01 * math.log(pi01)
            if n00 > 0 and pi01 < 1:
                lr_terms += n00 * math.log(1 - pi01)

        # Conditional state 1 terms: n10*ln(1-π11) + n11*ln(π11)
        if n1 > 0:
            if n11 > 0 and pi11 > 0:
                lr_terms += n11 * math.log(pi11)
            if n10 > 0 and pi11 < 1:
                lr_terms += n10 * math.log(1 - pi11)

        # Unconditional terms: -(n01+n11)*ln(π) - (n00+n10)*ln(1-π)
        if n_breach > 0 and pi > 0:
            lr_terms -= n_breach * math.log(pi)
        if (total - n_breach) > 0 and pi < 1:
            lr_terms -= (total - n_breach) * math.log(1 - pi)

        lr = 2.0 * lr_terms

        # Clamp small negative values to zero
        if lr < 0 and lr > -1e-10:
            lr = 0.0

        return Decimal(str(lr))
