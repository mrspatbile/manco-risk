"""PRIIPs Summary Risk Indicator (SRI) models.

Pure data models. No calculation or persistence logic.

Commission Delegated Regulation (EU) 2017/653 Annex II defines the SRI as a
combination of Market Risk Measure (MRM) and Credit Risk Measure (CRM) classes.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from manco_risk.risk.priips.constants import (
    CRM_MAX_CLASS,
    CRM_MIN_CLASS,
    MRM_MAX_CLASS,
    MRM_MIN_CLASS,
    SRI_MAX_CLASS,
    SRI_MIN_CLASS,
)


class SRIInput(BaseModel):
    """Input to SRI calculation engine.

    Minimal, methodology-agnostic input representing a single SRI observation
    for a product at a point in time.

    The engine will look up the SRI class from the regulatory combination table.
    No duplication of derived state.

    Fields:
    - product_id: Product identifier (string, e.g., "UCITS_Balanced").
    - valuation_date: Snapshot date (ISO 8601).
    - mrm_class: Market Risk Measure class (1-7, pre-computed).
    - crm_class: Credit Risk Measure class (1-6, optional; None if not applicable).

    Invariants:
    - product_id must be non-empty.
    - mrm_class must be in [1, 7].
    - crm_class must be in [1, 6] or None.
    """

    product_id: str
    valuation_date: date
    mrm_class: int
    crm_class: int | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Product ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("product_id must be non-empty")
        return v.strip()

    @field_validator("mrm_class")
    @classmethod
    def validate_mrm_class(cls, v: int) -> int:
        """MRM class must be in [1, 7]."""
        if v < MRM_MIN_CLASS or v > MRM_MAX_CLASS:
            raise ValueError(f"mrm_class must be in [{MRM_MIN_CLASS}, {MRM_MAX_CLASS}], got {v}")
        return v

    @field_validator("crm_class")
    @classmethod
    def validate_crm_class(cls, v: int | None) -> int | None:
        """CRM class must be in [1, 6] or None."""
        if v is not None and (v < CRM_MIN_CLASS or v > CRM_MAX_CLASS):
            raise ValueError(
                f"crm_class must be in [{CRM_MIN_CLASS}, {CRM_MAX_CLASS}] or None, got {v}"
            )
        return v


class SRIResult(BaseModel):
    """Result of SRI calculation.

    Combines MRM and CRM classes into final SRI class (1-7) using the regulatory
    combination table from Delegated Regulation 2017/653 Annex II.

    All fields are populated by the engine and stored for reporting convenience.
    This model is a simple immutable DTO with minimal defensive validation.

    Fields:
    - product_id: Product identifier.
    - valuation_date: Snapshot date.
    - mrm_class: Market Risk Measure class (1-7, from input).
    - crm_class: Credit Risk Measure class (1-6, normalized; None → CRM_DEFAULT_CLASS).
    - sri_class: Summary Risk Indicator class (1-7, calculated from table).

    Invariants (defensive checks):
    - product_id must be non-empty.
    - mrm_class must be in [1, 7].
    - crm_class must be in [1, 6].
    - sri_class must be in [1, 7].
    """

    product_id: str
    valuation_date: date
    mrm_class: int
    crm_class: int
    sri_class: int

    model_config = ConfigDict(frozen=True)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        """Product ID must be non-empty (defensive check)."""
        if not v or not v.strip():
            raise ValueError("product_id must be non-empty")
        return v.strip()

    @field_validator("mrm_class")
    @classmethod
    def validate_mrm_class(cls, v: int) -> int:
        """MRM class must be in [1, 7] (defensive check)."""
        if v < MRM_MIN_CLASS or v > MRM_MAX_CLASS:
            raise ValueError(f"mrm_class must be in [{MRM_MIN_CLASS}, {MRM_MAX_CLASS}], got {v}")
        return v

    @field_validator("crm_class")
    @classmethod
    def validate_crm_class(cls, v: int) -> int:
        """CRM class must be in [1, 6] (defensive check)."""
        if v < CRM_MIN_CLASS or v > CRM_MAX_CLASS:
            raise ValueError(f"crm_class must be in [{CRM_MIN_CLASS}, {CRM_MAX_CLASS}], got {v}")
        return v

    @field_validator("sri_class")
    @classmethod
    def validate_sri_class(cls, v: int) -> int:
        """SRI class must be in [1, 7] (defensive check)."""
        if v < SRI_MIN_CLASS or v > SRI_MAX_CLASS:
            raise ValueError(f"sri_class must be in [{SRI_MIN_CLASS}, {SRI_MAX_CLASS}], got {v}")
        return v
