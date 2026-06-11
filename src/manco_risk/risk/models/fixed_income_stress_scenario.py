"""Stress scenario definition for fixed-income stress testing.

Encapsulates a single fixed-income stress scenario with independent rate and
spread shock components. Both bps fields are always present; zero means that
shock component is not applied.

Unlike the equity StressScenario (single shock_rate), fixed-income scenarios
carry separate rate_shock_bps and spread_shock_bps because rate risk and credit
spread risk are independently parameterised.

shock_type is an audit/documentation label only. The pricer branches on whether
the bps values are zero or non-zero, not on shock_type.
"""

from pydantic import BaseModel, ConfigDict, field_validator


class FixedIncomeStressScenario(BaseModel):
    """A stress scenario for fixed-income portfolio stress testing.

    Defines:
    - scenario identification and naming
    - scenario type (hypothetical, historical, regulatory, etc.)
    - scenario source (manager-defined, regulatory, internal, etc.)
    - shock_type: audit label, e.g. "RATE_SHOCK", "SPREAD_SHOCK", "COMBINED"
    - rate_shock_bps: parallel yield shock in integer basis points
    - spread_shock_bps: credit spread shock in integer basis points
    - description for methodology documentation

    Fields:
    - scenario_id: Unique scenario identifier, e.g., "FI_RATE_UP_100"
    - scenario_name: Human-readable scenario name
    - scenario_type: Type of scenario, e.g., "HYPOTHETICAL", "HISTORICAL"
    - scenario_source: Source of the scenario, e.g., "MANAGER_DEFINED"
    - shock_type: Audit label, e.g., "RATE_SHOCK", "SPREAD_SHOCK", "COMBINED"
    - rate_shock_bps: Yield shock in bps; positive = yield up (price down)
    - spread_shock_bps: Spread shock in bps; positive = spread widens (price down)
    - description: Methodology documentation

    Sign conventions:
    - positive rate_shock_bps: yield rises, bond price falls, negative rate P&L (loss)
    - negative rate_shock_bps: yield falls, bond price rises, positive rate P&L (gain)
    - positive spread_shock_bps: spread widens, bond price falls, negative credit P&L (loss)
    - zero bps: that shock component is not applied; corresponding duration not required

    Units:
    - rate_shock_bps and spread_shock_bps: integer basis points
      e.g., 100 = 100 bps = 1.0% shift; -50 = -50 bps = -0.5% shift

    Immutability:
    - FixedIncomeStressScenario is frozen; caller creates once, pricer reads only.
    """

    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    shock_type: str
    rate_shock_bps: int
    spread_shock_bps: int
    description: str

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "scenario_id",
        "scenario_name",
        "scenario_type",
        "scenario_source",
        "shock_type",
        "description",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        """All string fields must be non-empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must be non-empty")
        return v.strip()
