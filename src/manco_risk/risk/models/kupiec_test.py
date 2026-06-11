"""Kupiec unconditional coverage test result model.

Represents the output of the Kupiec POF (Proportion of Failures) test
for VaR model backtesting.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class KupiecTestResult(BaseModel):
    """Result of Kupiec unconditional coverage test.

    The Kupiec POF test evaluates whether the observed number of VaR breaches
    is consistent with the expected breach probability under the model.

    Hypothesis:
    - H₀ (null): Observed breach count is consistent with expected probability
    - H₁ (alternative): Observed breach count is inconsistent

    Test statistic:
    - LR_uc = 2 * (ln L₁ - ln L₀)
      where L₁ = likelihood under observed breach probability
            L₀ = likelihood under expected breach probability
    - Under H₀, LR_uc ~ χ²(1)

    Fields:
    - num_observations: Number of valid aligned VaR/P&L observations.
    - num_breaches: Observed number of VaR breaches.
    - expected_breach_probability: Expected breach probability (1 - confidence_level).
    - observed_breach_probability: Observed breach ratio (num_breaches / num_observations).
    - lr_statistic: Likelihood ratio test statistic.
    - p_value: P-value from chi-square distribution (1 df).
    - alpha: Significance level for hypothesis test (default 0.05).
    - reject_null: True if p_value < alpha (reject H₀, model is inconsistent).

    Sign convention:
    - All probabilities are in [0, 1] as decimal ratios.
    - Example: 5% = Decimal("0.05")

    Invariants:
    - num_observations > 0
    - 0 <= num_breaches <= num_observations
    - 0 < expected_breach_probability < 1
    - 0 <= observed_breach_probability <= 1
    - 0 <= lr_statistic
    - 0 <= p_value <= 1
    - 0 < alpha < 1
    - reject_null = (p_value < alpha)
    """

    num_observations: int
    num_breaches: int
    expected_breach_probability: Decimal
    observed_breach_probability: Decimal
    lr_statistic: Decimal
    p_value: Decimal
    alpha: Decimal
    reject_null: bool

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

    @field_validator("num_breaches")
    @classmethod
    def validate_breaches_not_exceed_observations(cls, v: int, info) -> int:
        """Number of breaches must not exceed observations."""
        if "num_observations" in info.data and v > info.data["num_observations"]:
            raise ValueError(
                f"Number of breaches ({v}) cannot exceed "
                f"number of observations ({info.data['num_observations']})"
            )
        return v

    @field_validator("expected_breach_probability")
    @classmethod
    def validate_expected_breach_probability(cls, v: Decimal) -> Decimal:
        """Expected breach probability must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Expected breach probability must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("observed_breach_probability")
    @classmethod
    def validate_observed_breach_probability(cls, v: Decimal) -> Decimal:
        """Observed breach probability must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"Observed breach probability must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("observed_breach_probability")
    @classmethod
    def validate_observed_equals_ratio(cls, v: Decimal, info) -> Decimal:
        """Observed breach probability must equal num_breaches / num_observations."""
        if "num_observations" in info.data and "num_breaches" in info.data:
            num_obs = info.data["num_observations"]
            num_breaches = info.data["num_breaches"]
            expected_ratio = Decimal(num_breaches) / Decimal(num_obs)
            # Use small tolerance for decimal precision
            if abs(v - expected_ratio) > Decimal("0.000001"):
                raise ValueError(
                    f"Observed breach probability {v} must equal "
                    f"num_breaches / num_observations ({expected_ratio})"
                )
        return v

    @field_validator("lr_statistic")
    @classmethod
    def validate_lr_statistic(cls, v: Decimal) -> Decimal:
        """Likelihood ratio statistic must be non-negative."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0"):
            raise ValueError(f"Likelihood ratio statistic must be non-negative, got {v_decimal}")
        return v_decimal

    @field_validator("p_value")
    @classmethod
    def validate_p_value(cls, v: Decimal) -> Decimal:
        """P-value must be in [0, 1]."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal < Decimal("0") or v_decimal > Decimal("1"):
            raise ValueError(f"P-value must be in [0, 1], got {v_decimal}")
        return v_decimal

    @field_validator("alpha")
    @classmethod
    def validate_alpha(cls, v: Decimal) -> Decimal:
        """Significance level must be in (0, 1)."""
        v_decimal = v if isinstance(v, Decimal) else Decimal(str(v))
        if v_decimal <= Decimal("0") or v_decimal >= Decimal("1"):
            raise ValueError(f"Alpha must be in (0, 1), got {v_decimal}")
        return v_decimal

    @field_validator("reject_null")
    @classmethod
    def validate_reject_null(cls, v: bool, info) -> bool:
        """Reject null flag must match p_value < alpha."""
        if "p_value" in info.data and "alpha" in info.data:
            expected_reject = info.data["p_value"] < info.data["alpha"]
            if v != expected_reject:
                raise ValueError(
                    f"reject_null must be {expected_reject} "
                    f"given p_value={info.data['p_value']} and alpha={info.data['alpha']}"
                )
        return v
