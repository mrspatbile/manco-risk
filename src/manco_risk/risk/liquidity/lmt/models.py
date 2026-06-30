"""LMT (Liquidity Management Tools) domain models.

Typed models for LMT simulation: configuration, monthly inputs, state tracking,
and 12-month results. No calculation logic; validation only.

Conventions:
- Rates, thresholds, and ratios stored as Decimal (e.g., 0.10 = 10%, 1.0 = 100%)
- Monetary values stored as Decimal (non-negative)
- Month indices are 0-based (0 = month 1, 1 = month 2, etc.)
- Backlog and deferred amounts must be non-negative and consistent
- Contagion and suspension parameters are explicit; no hidden behavior
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

if TYPE_CHECKING:
    from manco_risk.risk.liquidity.models import (
        InvestorConcentrationResult,
        PortfolioLiquidityProfileResult,
    )


class ScenarioVariant(str, Enum):
    """LMT simulation scenario type.

    Enumerates variants of the 12-month simulation.

    Values:
    - BASE: Standard scenario using input monthly redemptions as-is.
    - LARGEST_INVESTOR: Largest investor redemption scenario.
      Month 0 redemption is replaced with largest investor amount from Issue #6.
    """

    BASE = "base"
    LARGEST_INVESTOR = "largest_investor"


class GateTriggerConfig(BaseModel):
    """Redemption gate trigger configuration.

    Defines conditions under which redemption gates are applied to limit
    the amount redeemed on a dealing date.

    Fields:
    - enabled: Whether gates can be applied in simulation.
    - coverage_ratio_threshold: Trigger gate if coverage_ratio < threshold.
      E.g., 1.0 means trigger if available liquidity < redemption demand.
      E.g., 1.2 means trigger if coverage < 120%.
    - max_gate_ratio: Maximum fraction of redemptions that can be deferred.
      E.g., 0.5 means up to 50% of redemptions can be gated.
      Must be in (0, 1] if enabled.
    - description: Optional description for audit/documentation.
    """

    enabled: bool
    coverage_ratio_threshold: Decimal
    max_gate_ratio: Decimal
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("coverage_ratio_threshold")
    @classmethod
    def validate_coverage_ratio_threshold(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("coverage_ratio_threshold must be positive")
        return v

    @field_validator("max_gate_ratio")
    @classmethod
    def validate_max_gate_ratio(cls, v: Decimal) -> Decimal:
        if v <= 0 or v > 1:
            raise ValueError("max_gate_ratio must be in (0, 1]")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("description must be non-empty or None")
        return v.strip() if v else None


class SwingPricingConfig(BaseModel):
    """Swing pricing trigger and calibration configuration.

    Defines when and how swing pricing adjusts the dealing NAV to pass
    estimated liquidity costs to transacting investors.

    Fields:
    - enabled: Whether swing pricing is applied.
    - trigger_threshold: Trigger swing if net redemptions exceed this
      fraction of NAV. E.g., 0.10 = trigger if redemptions > 10% of NAV.
      Must be in [0, 1].
    - max_swing_factor: Maximum swing factor to apply. E.g., 0.02 = up to 2%.
      Must be in [0, 1].
    - cost_basis: How to calculate swing cost: "nav" (% of fund NAV) or
      "flow" (% of redemption flow). Typically "nav" per ESMA guidance.
    - description: Optional description.
    """

    enabled: bool
    trigger_threshold: Decimal
    max_swing_factor: Decimal
    cost_basis: str
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("trigger_threshold")
    @classmethod
    def validate_trigger_threshold(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("trigger_threshold must be in [0, 1]")
        return v

    @field_validator("max_swing_factor")
    @classmethod
    def validate_max_swing_factor(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError("max_swing_factor must be in [0, 1]")
        return v

    @field_validator("cost_basis")
    @classmethod
    def validate_cost_basis(cls, v: str) -> str:
        if v not in ("nav", "flow"):
            raise ValueError("cost_basis must be 'nav' or 'flow'")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("description must be non-empty or None")
        return v.strip() if v else None


class SuspensionConfig(BaseModel):
    """Suspension trigger and governance configuration.

    Defines exceptional conditions under which fund subscriptions/redemptions
    may be suspended, and procedures for suspension review and reopening.

    Fields:
    - enabled: Whether suspension logic is applied.
    - trigger_criteria: List of conditions that can trigger suspension.
      Examples: "liquidity_shortfall", "nav_unreliable", "market_disruption".
      Must be non-empty if enabled.
    - review_frequency_days: How often suspension status is reviewed (days).
      Must be positive.
    - max_suspension_days: Maximum suspension duration (days). None = no limit.
      If set, must be positive.
    - requires_investor_notification: Must investors be notified of suspension?
    - requires_nca_notification: Must regulator be notified of suspension?
    - description: Optional description.
    """

    enabled: bool
    trigger_criteria: list[str]
    review_frequency_days: int
    max_suspension_days: int | None = None
    requires_investor_notification: bool = False
    requires_nca_notification: bool = False
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("trigger_criteria")
    @classmethod
    def validate_trigger_criteria(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("trigger_criteria must be non-empty")
        for criterion in v:
            if not criterion or not criterion.strip():
                raise ValueError("Each trigger_criteria entry must be non-empty")
        return [c.strip() for c in v]

    @field_validator("review_frequency_days")
    @classmethod
    def validate_review_frequency_days(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("review_frequency_days must be positive")
        return v

    @field_validator("max_suspension_days")
    @classmethod
    def validate_max_suspension_days(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("max_suspension_days must be positive or None")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("description must be non-empty or None")
        return v.strip() if v else None


class ContagionConfig(BaseModel):
    """Cross-fund contagion linkage configuration.

    Defines how redemption stress in linked funds may trigger additional
    redemption pressure in this fund (contagion effect).

    Fields:
    - enabled: Whether contagion logic is applied.
      If False, all other fields are ignored.
    - contagion_trigger_threshold: If linked fund coverage ratio drops below
      this, contagion is triggered. E.g., 1.0 = trigger if coverage < 100%.
      Must be positive if enabled.
    - contagion_multiplier: Multiplier on linked fund redemptions to estimate
      contagion impact. E.g., 1.5 = 150% of linked fund redemption flows.
      Must be >= 1.0 if enabled.
    - linked_fund_ids: Optional list of linked fund identifiers.
      If provided, only these funds trigger contagion.
      If None/empty and enabled, use global linked fund list (handled externally).
    - description: Optional description.
    """

    enabled: bool
    contagion_trigger_threshold: Decimal | None = None
    contagion_multiplier: Decimal | None = None
    linked_fund_ids: list[str] | None = None
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("contagion_trigger_threshold")
    @classmethod
    def validate_contagion_trigger_threshold(cls, v: Decimal | None, info) -> Decimal | None:
        if info.data.get("enabled"):
            if v is None:
                raise ValueError("contagion_trigger_threshold must be set if contagion is enabled")
            if v <= 0:
                raise ValueError("contagion_trigger_threshold must be positive")
        return v

    @field_validator("contagion_multiplier")
    @classmethod
    def validate_contagion_multiplier(cls, v: Decimal | None, info) -> Decimal | None:
        if info.data.get("enabled"):
            if v is None:
                raise ValueError("contagion_multiplier must be set if contagion is enabled")
            if v < 1:
                raise ValueError("contagion_multiplier must be >= 1.0")
        return v

    @field_validator("linked_fund_ids")
    @classmethod
    def validate_linked_fund_ids(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if not v:
                raise ValueError("linked_fund_ids must be non-empty or None")
            for fund_id in v:
                if not fund_id or not fund_id.strip():
                    raise ValueError("Each fund ID must be non-empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("description must be non-empty or None")
        return v.strip() if v else None


class LMTScenarioConfig(BaseModel):
    """Complete LMT scenario configuration.

    Groups all LMT tool configurations (gates, swing, suspension, contagion)
    into a single scenario definition.

    Fields:
    - gate_config: Redemption gate configuration.
    - swing_config: Swing pricing configuration.
    - suspension_config: Suspension configuration.
    - contagion_config: Contagion linkage configuration.
    """

    gate_config: GateTriggerConfig
    swing_config: SwingPricingConfig
    suspension_config: SuspensionConfig
    contagion_config: ContagionConfig

    model_config = ConfigDict(frozen=True)


class LiquiditySnapshot(BaseModel):
    """Monthly liquidity snapshot from Issue #6 analytics.

    Pre-computed by caller (Issue #6 liquidity engines).
    Orchestrator reads only; never fetches or computes liquidity data.

    Fields:
    - valuation_date: Date of snapshot.
    - fund_nav: Fund NAV at snapshot (Decimal, > 0).
    - available_liquidity: Liquid assets (Decimal, >= 0).
    - coverage_ratio: available_liquidity / redemption_demand (Decimal, >= 0).
    - portfolio_liquidity_profile: TTL bucket distribution (for traceability).
    - investor_concentration: Investor metrics, optional (for largest-investor scenarios).
    """

    valuation_date: date
    fund_nav: Decimal
    available_liquidity: Decimal
    coverage_ratio: Decimal
    portfolio_liquidity_profile: "PortfolioLiquidityProfileResult"  # noqa: F821
    investor_concentration: "InvestorConcentrationResult | None" = None  # noqa: F821

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_nav")
    @classmethod
    def validate_fund_nav(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("fund_nav must be positive")
        return v

    @field_validator("available_liquidity", "coverage_ratio")
    @classmethod
    def validate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v


class MonthlyRedemptionInput(BaseModel):
    """Single month's redemption scenario input.

    Represents redemption demand and other cash outflows for one month
    of the simulation.

    Fields:
    - month_index: 0-based month index (0 = month 1, 1 = month 2, etc.).
    - redemption_amount: Redemption requests in base currency (Decimal, >= 0).
    - margin_call_amount: Margin calls or other liability outflows (Decimal, >= 0).
    - description: Optional scenario description.
    """

    month_index: int
    redemption_amount: Decimal
    margin_call_amount: Decimal = Decimal("0")
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("month_index")
    @classmethod
    def validate_month_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError("month_index must be non-negative")
        return v

    @field_validator("redemption_amount")
    @classmethod
    def validate_redemption_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("redemption_amount must be non-negative")
        return v

    @field_validator("margin_call_amount")
    @classmethod
    def validate_margin_call_amount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("margin_call_amount must be non-negative")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("description must be non-empty or None")
        return v.strip() if v else None


class BacklogState(BaseModel):
    """Redemption backlog state for a single month.

    Tracks how much redemption demand could not be met in the current month
    and is deferred to future months.

    Fields:
    - month_index: Month this backlog applies to.
    - beginning_backlog: Backlog carried forward from prior month (Decimal, >= 0).
    - new_redemptions: New redemption requests in this month (Decimal, >= 0).
    - total_redemptions_due: Sum of beginning + new (must equal exactly).
    - redeemed_in_month: Amount actually redeemed (Decimal, >= 0, <= total_due).
    - ending_backlog: Amount deferred to next month (must equal total_due - redeemed).
    - deferral_reason: Why redemptions were deferred (e.g., "gate", "insufficient_liquidity").
    """

    month_index: int
    beginning_backlog: Decimal
    new_redemptions: Decimal
    total_redemptions_due: Decimal
    redeemed_in_month: Decimal
    ending_backlog: Decimal
    deferral_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("month_index")
    @classmethod
    def validate_month_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError("month_index must be non-negative")
        return v

    @field_validator("beginning_backlog", "new_redemptions", "redeemed_in_month")
    @classmethod
    def validate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v

    @field_validator("total_redemptions_due", "ending_backlog")
    @classmethod
    def validate_total_and_ending(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v

    @field_validator("deferral_reason")
    @classmethod
    def validate_deferral_reason(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("deferral_reason must be non-empty or None")
        return v.strip() if v else None

    @model_validator(mode="after")
    def validate_backlog_accounting(self) -> "BacklogState":
        """Verify accounting: total = beginning + new; ending = total - redeemed."""
        expected_total = self.beginning_backlog + self.new_redemptions
        if abs(self.total_redemptions_due - expected_total) > Decimal("0.01"):
            raise ValueError(
                f"total_redemptions_due mismatch: "
                f"expected {expected_total}, got {self.total_redemptions_due}"
            )

        expected_ending = self.total_redemptions_due - self.redeemed_in_month
        if abs(self.ending_backlog - expected_ending) > Decimal("0.01"):
            raise ValueError(
                f"ending_backlog mismatch: expected {expected_ending}, got {self.ending_backlog}"
            )

        if self.redeemed_in_month > self.total_redemptions_due + Decimal("0.01"):
            raise ValueError("redeemed_in_month cannot exceed total_redemptions_due")

        return self


class LMTMonthlyResult(BaseModel):
    """Single month's LMT simulation result.

    Complete outcome for one month: liquidity state, LMT activations,
    NAV impact, and backlog progression.

    Fields:
    - month_index: Month this result covers (0-based).
    - valuation_date: Date of valuation (start of month).
    - fund_nav: Fund NAV at start of month (Decimal, > 0).
    - redemption_amount: Total redemption demand (Decimal, >= 0).
    - available_liquidity: Available liquid assets before LMT (Decimal, >= 0).
    - coverage_ratio: available_liquidity / redemption_amount.
      Special cases: if redemption_amount == 0, ratio is None or infinity.
    - gate_activated: Whether redemption gate was triggered.
    - gate_deferred_amount: Amount deferred by gate (Decimal, >= 0).
    - swing_pricing_activated: Whether swing pricing was triggered.
    - swing_factor_applied: Actual swing factor applied (Decimal, [0, 1] if activated, else 0).
    - suspension_activated: Whether fund suspension was triggered.
    - suspension_reason: Why suspension was triggered (required if activated).
    - contagion_triggered: Whether contagion linkage activated.
    - ending_nav: Fund NAV at end of month (Decimal, >= 0).
    - backlog_amount: Redemption backlog carried to next month (Decimal, >= 0).
    - deferral_reason: Why redemptions were deferred, if any (e.g., "gate", "suspension").
    - warnings: Any warnings or notes (list of strings).
    """

    month_index: int
    valuation_date: date
    fund_nav: Decimal
    redemption_amount: Decimal
    available_liquidity: Decimal
    coverage_ratio: Decimal | None
    gate_activated: bool
    gate_deferred_amount: Decimal
    swing_pricing_activated: bool
    swing_factor_applied: Decimal
    suspension_activated: bool
    suspension_reason: str | None
    contagion_triggered: bool
    ending_nav: Decimal
    backlog_amount: Decimal
    deferral_reason: str | None = None
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("month_index")
    @classmethod
    def validate_month_index(cls, v: int) -> int:
        if v < 0:
            raise ValueError("month_index must be non-negative")
        return v

    @field_validator("fund_nav", "ending_nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("NAV must be non-negative")
        return v

    @field_validator("redemption_amount", "available_liquidity", "backlog_amount")
    @classmethod
    def validate_amounts(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v

    @field_validator("coverage_ratio")
    @classmethod
    def validate_coverage_ratio(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v < 0:
            raise ValueError("coverage_ratio must be non-negative")
        return v

    @field_validator("gate_deferred_amount", "swing_factor_applied")
    @classmethod
    def validate_gate_and_swing(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("amount/factor must be non-negative")
        return v

    @field_validator("swing_factor_applied")
    @classmethod
    def validate_swing_factor_range(cls, v: Decimal) -> Decimal:
        if v > 1:
            raise ValueError("swing_factor_applied must be <= 1.0")
        return v

    @field_validator("suspension_reason")
    @classmethod
    def validate_suspension_reason(cls, v: str | None, info) -> str | None:
        if info.data.get("suspension_activated") and not v:
            raise ValueError("suspension_reason required if suspension_activated=True")
        if not info.data.get("suspension_activated") and v:
            raise ValueError("suspension_reason should be None if suspension_activated=False")
        if v is not None and not v.strip():
            raise ValueError("suspension_reason must be non-empty or None")
        return v.strip() if v else None

    @field_validator("warnings")
    @classmethod
    def validate_warnings(cls, v: list[str]) -> list[str]:
        for warning in v:
            if not warning or not warning.strip():
                raise ValueError("Each warning must be non-empty")
        return v

    @model_validator(mode="after")
    def validate_gate_deferred_vs_redemption(self) -> "LMTMonthlyResult":
        """Gate deferred amount should not exceed redemption amount."""
        if self.gate_deferred_amount > self.redemption_amount + Decimal("0.01"):
            raise ValueError("gate_deferred_amount cannot exceed redemption_amount")
        return self


class LMTSimulationInput(BaseModel):
    """Complete LMT simulation input for 12-month pathway.

    Specifies the fund, initial state, LMT configuration, and monthly
    redemption scenario for a full simulation run.

    Fields:
    - fund_id: Fund identifier (positive integer).
    - valuation_date: Simulation start date.
    - fund_nav: Fund NAV at simulation start (Decimal, > 0).
    - scenario_config: LMT configuration (gates, swing, suspension, contagion).
    - monthly_redemptions: Monthly redemption inputs for each month.
      Month indices must be sequential (0, 1, 2, ..., N-1).
    """

    fund_id: int
    valuation_date: date
    fund_nav: Decimal
    scenario_config: LMTScenarioConfig
    monthly_redemptions: list[MonthlyRedemptionInput]

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fund_id must be positive")
        return v

    @field_validator("fund_nav")
    @classmethod
    def validate_fund_nav(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("fund_nav must be positive")
        return v

    @field_validator("monthly_redemptions")
    @classmethod
    def validate_monthly_redemptions(
        cls, v: list[MonthlyRedemptionInput]
    ) -> list[MonthlyRedemptionInput]:
        if not v:
            raise ValueError("monthly_redemptions must be non-empty")
        if len(v) != 12:
            raise ValueError(f"monthly_redemptions must contain exactly 12 months, got {len(v)}")
        return v

    @model_validator(mode="after")
    def validate_monthly_indices_sequential(self) -> "LMTSimulationInput":
        """Verify monthly indices are sequential starting from 0."""
        indices = sorted([r.month_index for r in self.monthly_redemptions])
        expected = list(range(12))  # Always 12 months
        if indices != expected:
            raise ValueError(
                "month_index values must be sequential (0, 1, 2, ..., 11) for 12 months"
            )
        return self


class LMTSimulationResult(BaseModel):
    """Complete 12-month LMT simulation result.

    Aggregated outcome across all simulation months, plus monthly detail.
    Reporting-ready: can be consumed by reporting, visualization, and UI layers.

    Fields:
    - fund_id: Fund identifier.
    - valuation_date: Simulation start date.
    - initial_nav: NAV at simulation start (Decimal, > 0).
    - final_nav: NAV at end of simulation (Decimal, >= 0).
    - total_redemptions: Sum of all monthly redemptions (Decimal, >= 0).
    - total_backlog_accumulated: Peak backlog reached (Decimal, >= 0).
    - months_with_backlog: Count of months with deferred redemptions (>= 0).
    - gate_activation_count: Number of months gate was triggered (>= 0).
    - swing_pricing_activation_count: Number of months swing was triggered (>= 0).
    - suspension_activation_count: Number of months suspension was triggered (>= 0).
    - contagion_triggered_count: Number of months contagion was triggered (>= 0).
    - monthly_results: List of monthly outcomes (one per month).
    - warnings: Simulation-level warnings.
    """

    fund_id: int
    valuation_date: date
    initial_nav: Decimal
    final_nav: Decimal
    total_redemptions: Decimal
    total_backlog_accumulated: Decimal
    months_with_backlog: int
    gate_activation_count: int
    swing_pricing_activation_count: int
    suspension_activation_count: int
    contagion_triggered_count: int
    monthly_results: list[LMTMonthlyResult]
    warnings: list[str] = []

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_id")
    @classmethod
    def validate_fund_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fund_id must be positive")
        return v

    @field_validator("initial_nav")
    @classmethod
    def validate_initial_nav(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("initial_nav must be positive")
        return v

    @field_validator("final_nav", "total_redemptions", "total_backlog_accumulated")
    @classmethod
    def validate_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("value must be non-negative")
        return v

    @field_validator(
        "months_with_backlog",
        "gate_activation_count",
        "swing_pricing_activation_count",
        "suspension_activation_count",
        "contagion_triggered_count",
    )
    @classmethod
    def validate_counts(cls, v: int) -> int:
        if v < 0:
            raise ValueError("count must be non-negative")
        return v

    @field_validator("monthly_results")
    @classmethod
    def validate_monthly_results(cls, v: list[LMTMonthlyResult]) -> list[LMTMonthlyResult]:
        if not v:
            raise ValueError("monthly_results must be non-empty")
        return v

    @field_validator("warnings")
    @classmethod
    def validate_warnings(cls, v: list[str]) -> list[str]:
        for warning in v:
            if not warning or not warning.strip():
                raise ValueError("Each warning must be non-empty")
        return v

    @model_validator(mode="after")
    def validate_activation_counts(self) -> "LMTSimulationResult":
        """Verify activation counts don't exceed number of months."""
        num_months = len(self.monthly_results)
        if self.gate_activation_count > num_months:
            raise ValueError("gate_activation_count cannot exceed number of months")
        if self.swing_pricing_activation_count > num_months:
            raise ValueError("swing_pricing_activation_count cannot exceed number of months")
        if self.suspension_activation_count > num_months:
            raise ValueError("suspension_activation_count cannot exceed number of months")
        if self.contagion_triggered_count > num_months:
            raise ValueError("contagion_triggered_count cannot exceed number of months")
        return self

    @model_validator(mode="after")
    def validate_monthly_indices_sequential(self) -> "LMTSimulationResult":
        """Verify monthly results are sequential by index."""
        indices = [r.month_index for r in self.monthly_results]
        expected = list(range(len(self.monthly_results)))
        if indices != expected:
            raise ValueError("monthly_results must have sequential month_index values")
        return self

    @model_validator(mode="after")
    def validate_activation_counts_match_months(self) -> "LMTSimulationResult":
        """Verify activation counts match actual activations in monthly results."""
        actual_gate = sum(1 for r in self.monthly_results if r.gate_activated)
        if self.gate_activation_count != actual_gate:
            raise ValueError(
                f"gate_activation_count mismatch: "
                f"expected {actual_gate}, got {self.gate_activation_count}"
            )

        actual_swing = sum(1 for r in self.monthly_results if r.swing_pricing_activated)
        if self.swing_pricing_activation_count != actual_swing:
            raise ValueError(
                f"swing_pricing_activation_count mismatch: "
                f"expected {actual_swing}, got {self.swing_pricing_activation_count}"
            )

        actual_suspension = sum(1 for r in self.monthly_results if r.suspension_activated)
        if self.suspension_activation_count != actual_suspension:
            raise ValueError(
                f"suspension_activation_count mismatch: "
                f"expected {actual_suspension}, got {self.suspension_activation_count}"
            )

        actual_contagion = sum(1 for r in self.monthly_results if r.contagion_triggered)
        if self.contagion_triggered_count != actual_contagion:
            raise ValueError(
                f"contagion_triggered_count mismatch: "
                f"expected {actual_contagion}, got {self.contagion_triggered_count}"
            )

        return self
