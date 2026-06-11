"""Stress scenario definition for equity-like stress testing.

Encapsulates a single stress scenario: scenario metadata, shock type,
shock rate, and supporting documentation.

A stress scenario is supplied by the caller and applied by the engine
to a fixed portfolio. The engine does not hard-code scenarios.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class StressScenario(BaseModel):
    """A stress scenario for equity-like portfolio stress testing.

    Defines:
    - scenario identification and naming
    - scenario type (hypothetical, historical, reverse, etc.)
    - scenario source (manager-defined, regulatory, internal, etc.)
    - shock type (parallel equity, etc.)
    - shock rate (decimal, e.g., -0.20 for 20% down)
    - description for methodology documentation

    Fields:
    - scenario_id: Unique scenario identifier, e.g., "EQ_PARALLEL_20"
    - scenario_name: Human-readable scenario name
    - scenario_type: Type of scenario, e.g., "HYPOTHETICAL", "HISTORICAL", "REVERSE"
    - scenario_source: Source of the scenario, e.g., "MANAGER_DEFINED", "REGULATORY", "INTERNAL"
    - shock_type: Type of shock applied, e.g., "PARALLEL_EQUITY"
    - shock_rate: Shock rate as a decimal, e.g., Decimal("-0.20") for 20% down
    - description: Documentation of the scenario, methodology, severity, frequency

    Sign convention:
    - Negative shock_rate = loss scenario (e.g., -0.20 = portfolio down 20%)
    - Positive shock_rate = gain scenario (e.g., +0.10 = portfolio up 10%)

    Immutability:
    - StressScenario is frozen; caller creates once, engine reads repeatedly
    """

    scenario_id: str
    scenario_name: str
    scenario_type: str
    scenario_source: str
    shock_type: str
    shock_rate: Decimal
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

    @field_validator("shock_rate", mode="before")
    @classmethod
    def validate_shock_rate(cls, v) -> Decimal:
        """Shock rate must be a valid Decimal."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except Exception as e:
            raise ValueError(f"shock_rate must be convertible to Decimal, got {v}: {e}")
