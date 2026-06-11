"""Christoffersen conditional coverage test result models.

Represents transition counts and statistical test outputs for the
Christoffersen test of VaR breach independence and conditional coverage.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TransitionMatrix(BaseModel):
    """Breach transition counts for 1-day-ahead prediction.

    Represents state transitions: non-breach (0) → non-breach (0), non-breach (0) → breach (1),
    breach (1) → non-breach (0), breach (1) → breach (1).

    Fields:
    - n00: Count of non-breach followed by non-breach.
    - n01: Count of non-breach followed by breach.
    - n10: Count of breach followed by non-breach.
    - n11: Count of breach followed by breach.

    Derived counts:
    - n0 = n00 + n01: Total observations where previous state was non-breach.
    - n1 = n10 + n11: Total observations where previous state was breach.
    - Total observations = n00 + n01 + n10 + n11.

    Invariants:
    - All counts >= 0
    - At least one transition observed (sum > 0) for meaningful independence test
    """

    n00: int
    n01: int
    n10: int
    n11: int

    model_config = ConfigDict(frozen=True)

    @field_validator("n00")
    @classmethod
    def validate_n00(cls, v: int) -> int:
        """n00 must be non-negative."""
        if v < 0:
            raise ValueError(f"n00 must be non-negative, got {v}")
        return v

    @field_validator("n01")
    @classmethod
    def validate_n01(cls, v: int) -> int:
        """n01 must be non-negative."""
        if v < 0:
            raise ValueError(f"n01 must be non-negative, got {v}")
        return v

    @field_validator("n10")
    @classmethod
    def validate_n10(cls, v: int) -> int:
        """n10 must be non-negative."""
        if v < 0:
            raise ValueError(f"n10 must be non-negative, got {v}")
        return v

    @field_validator("n11")
    @classmethod
    def validate_n11(cls, v: int) -> int:
        """n11 must be non-negative."""
        if v < 0:
            raise ValueError(f"n11 must be non-negative, got {v}")
        return v

    @property
    def n0(self) -> int:
        """Total observations where previous state was non-breach."""
        return self.n00 + self.n01

    @property
    def n1(self) -> int:
        """Total observations where previous state was breach."""
        return self.n10 + self.n11

    @property
    def total(self) -> int:
        """Total transition observations."""
        return self.n00 + self.n01 + self.n10 + self.n11


class ChristoffersenTestResult(BaseModel):
    """Result of Christoffersen conditional coverage test.

    The Christoffersen test combines:
    1. UC (Unconditional Coverage): tests breach probability
    2. Ind (Independence): tests for clustering of breaches
    3. CC (Conditional Coverage): joint test of UC + independence

    The test uses likelihood ratios and chi-square distributions.

    Fields:
    - num_observations: Number of valid aligned observations.
    - num_breaches: Observed number of breaches.
    - expected_breach_probability: Expected breach probability.
    - transition_matrix: Breach transition counts.
    - uc_test_statistic: UC likelihood ratio statistic ~ χ²(1).
    - uc_p_value: P-value for UC test.
    - ind_test_statistic: Independence likelihood ratio statistic ~ χ²(1).
    - ind_p_value: P-value for independence test.
    - cc_test_statistic: Combined UC + Ind statistic ~ χ²(2).
    - cc_p_value: P-value for conditional coverage test.
    - alpha: Significance level (default 0.05).
    - reject_uc: True if p_value_uc < alpha.
    - reject_ind: True if p_value_ind < alpha.
    - reject_cc: True if p_value_cc < alpha.

    Interpretation:
    - Reject UC: breach count inconsistent with expected probability
    - Reject Ind: breaches are clustered (not independent)
    - Reject CC: either UC or independence (or both) fails
    """

    num_observations: int
    num_breaches: int
    expected_breach_probability: Decimal
    transition_matrix: TransitionMatrix
    uc_test_statistic: Decimal
    uc_p_value: Decimal
    ind_test_statistic: Decimal
    ind_p_value: Decimal
    cc_test_statistic: Decimal
    cc_p_value: Decimal
    alpha: Decimal
    reject_uc: bool
    reject_ind: bool
    reject_cc: bool

    model_config = ConfigDict(frozen=True)

    @field_validator("num_observations")
    @classmethod
    def validate_num_observations(cls, v: int) -> int:
        """Number of observations must be positive."""
        if v <= 0:
            raise ValueError(f"Number of observations must be positive, got {v}")
        return v

    @field_validator("num_breaches")
    @classmethod
    def validate_num_breaches(cls, v: int) -> int:
        """Number of breaches must be non-negative."""
        if v < 0:
            raise ValueError(f"Number of breaches must be non-negative, got {v}")
        return v

    @field_validator("expected_breach_probability")
    @classmethod
    def validate_expected_breach_probability(cls, v: Decimal) -> Decimal:
        """Expected breach probability must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Expected breach probability must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("uc_test_statistic")
    @classmethod
    def validate_uc_test_statistic(cls, v: Decimal) -> Decimal:
        """UC test statistic must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"UC test statistic must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("uc_p_value")
    @classmethod
    def validate_uc_p_value(cls, v: Decimal) -> Decimal:
        """UC p-value must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"UC p-value must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("ind_test_statistic")
    @classmethod
    def validate_ind_test_statistic(cls, v: Decimal) -> Decimal:
        """Independence test statistic must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Independence test statistic must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("ind_p_value")
    @classmethod
    def validate_ind_p_value(cls, v: Decimal) -> Decimal:
        """Independence p-value must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"Independence p-value must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("cc_test_statistic")
    @classmethod
    def validate_cc_test_statistic(cls, v: Decimal) -> Decimal:
        """CC test statistic must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"CC test statistic must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("cc_p_value")
    @classmethod
    def validate_cc_p_value(cls, v: Decimal) -> Decimal:
        """CC p-value must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"CC p-value must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("alpha")
    @classmethod
    def validate_alpha(cls, v: Decimal) -> Decimal:
        """Significance level must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Alpha must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("reject_uc")
    @classmethod
    def validate_reject_uc(cls, v: bool, info) -> bool:
        """Reject UC flag must match uc_p_value < alpha."""
        if "uc_p_value" in info.data and "alpha" in info.data:
            expected_reject = info.data["uc_p_value"] < info.data["alpha"]
            if v != expected_reject:
                raise ValueError(
                    f"reject_uc must be {expected_reject} "
                    f"given uc_p_value={info.data['uc_p_value']} and alpha={info.data['alpha']}"
                )
        return v

    @field_validator("reject_ind")
    @classmethod
    def validate_reject_ind(cls, v: bool, info) -> bool:
        """Reject Ind flag must match ind_p_value < alpha."""
        if "ind_p_value" in info.data and "alpha" in info.data:
            expected_reject = info.data["ind_p_value"] < info.data["alpha"]
            if v != expected_reject:
                raise ValueError(
                    f"reject_ind must be {expected_reject} "
                    f"given ind_p_value={info.data['ind_p_value']} and alpha={info.data['alpha']}"
                )
        return v

    @field_validator("reject_cc")
    @classmethod
    def validate_reject_cc(cls, v: bool, info) -> bool:
        """Reject CC flag must match cc_p_value < alpha."""
        if "cc_p_value" in info.data and "alpha" in info.data:
            expected_reject = info.data["cc_p_value"] < info.data["alpha"]
            if v != expected_reject:
                raise ValueError(
                    f"reject_cc must be {expected_reject} "
                    f"given cc_p_value={info.data['cc_p_value']} and alpha={info.data['alpha']}"
                )
        return v
