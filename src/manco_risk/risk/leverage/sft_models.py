"""Securities financing transaction (SFT) input models and enums.

Pure data models for SFT leverage source.
Separates repo, reverse repo, and securities lending for leverage exposure calculation.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SFTType(str, Enum):
    """Type of securities financing transaction.

    REPO: Repurchase agreement (sale with buyback obligation).
    REVERSE_REPO: Reverse repurchase agreement (purchase with resale obligation).
    SECURITIES_LENDING: Securities lending transaction.
    """

    REPO = "REPO"
    REVERSE_REPO = "REVERSE_REPO"
    SECURITIES_LENDING = "SECURITIES_LENDING"


class SFTTreatment(str, Enum):
    """Treatment classification for SFT collateral.

    CASH_COLLATERAL_REINVESTED: Cash collateral has been reinvested.
    CASH_COLLATERAL_NOT_REINVESTED: Cash collateral held as cash, not reinvested.
    SECURITIES_COLLATERAL: Transaction collateralized with securities.
    OTHER: Other collateral arrangements.
    """

    CASH_COLLATERAL_REINVESTED = "CASH_COLLATERAL_REINVESTED"
    CASH_COLLATERAL_NOT_REINVESTED = "CASH_COLLATERAL_NOT_REINVESTED"
    SECURITIES_COLLATERAL = "SECURITIES_COLLATERAL"
    OTHER = "OTHER"


class SFTRecord(BaseModel):
    """Securities financing transaction record for leverage source identification.

    Tracks SFT-generated exposure and collateral composition.
    Identifies whether cash collateral has been reinvested as exposure.

    Fields:
    - sft_id: Unique SFT identifier (non-empty).
    - sft_type: Type of SFT (repo, reverse repo, or securities lending).
    - currency: SFT currency (non-empty).
    - market_value_base_ccy: Market value of SFT leg in base currency (non-negative).
    - cash_collateral_base_ccy: Cash collateral amount in base currency (non-negative).
    - securities_collateral_base_ccy: Securities collateral value in base currency (non-negative).
    - reinvested_cash_collateral_base_ccy: Portion of cash collateral that is reinvested (non-negative).
    - treatment: Collateral treatment classification.
    - description: Optional text description or reference.

    Invariants:
    - reinvested_cash_collateral_base_ccy <= cash_collateral_base_ccy
    - if treatment=CASH_COLLATERAL_REINVESTED, reinvested_cash_collateral_base_ccy > 0
    - if treatment=CASH_COLLATERAL_NOT_REINVESTED, reinvested_cash_collateral_base_ccy = 0
    """

    sft_id: str
    sft_type: SFTType
    currency: str
    market_value_base_ccy: Decimal
    cash_collateral_base_ccy: Decimal
    securities_collateral_base_ccy: Decimal
    reinvested_cash_collateral_base_ccy: Decimal
    treatment: SFTTreatment
    description: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("sft_id")
    @classmethod
    def validate_sft_id(cls, v: str) -> str:
        """SFT ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("sft_id must be non-empty")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency must be non-empty."""
        if not v or not v.strip():
            raise ValueError("currency must be non-empty")
        return v.strip()

    @field_validator("market_value_base_ccy")
    @classmethod
    def validate_market_value(cls, v: Decimal) -> Decimal:
        """Market value must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"market_value_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("cash_collateral_base_ccy")
    @classmethod
    def validate_cash_collateral(cls, v: Decimal) -> Decimal:
        """Cash collateral must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"cash_collateral_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("securities_collateral_base_ccy")
    @classmethod
    def validate_securities_collateral(cls, v: Decimal) -> Decimal:
        """Securities collateral must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"securities_collateral_base_ccy must be non-negative, got {v}")
        return v

    @field_validator("reinvested_cash_collateral_base_ccy")
    @classmethod
    def validate_reinvested_cash_collateral(cls, v: Decimal) -> Decimal:
        """Reinvested cash collateral must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"reinvested_cash_collateral_base_ccy must be non-negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_reinvested_not_greater_than_cash(self) -> "SFTRecord":
        """Reinvested cash collateral cannot exceed total cash collateral."""
        if self.reinvested_cash_collateral_base_ccy > self.cash_collateral_base_ccy:
            raise ValueError(
                f"reinvested_cash_collateral_base_ccy ({self.reinvested_cash_collateral_base_ccy}) "
                f"cannot exceed cash_collateral_base_ccy ({self.cash_collateral_base_ccy})"
            )
        return self

    @model_validator(mode="after")
    def validate_treatment_consistency(self) -> "SFTRecord":
        """Validate treatment matches reinvested cash collateral."""
        if self.treatment == SFTTreatment.CASH_COLLATERAL_REINVESTED:
            if self.reinvested_cash_collateral_base_ccy <= Decimal("0"):
                raise ValueError(
                    f"CASH_COLLATERAL_REINVESTED treatment requires "
                    f"reinvested_cash_collateral_base_ccy > 0, "
                    f"got {self.reinvested_cash_collateral_base_ccy}"
                )
        elif self.treatment == SFTTreatment.CASH_COLLATERAL_NOT_REINVESTED:
            if self.reinvested_cash_collateral_base_ccy != Decimal("0"):
                raise ValueError(
                    f"CASH_COLLATERAL_NOT_REINVESTED treatment requires "
                    f"reinvested_cash_collateral_base_ccy=0, "
                    f"got {self.reinvested_cash_collateral_base_ccy}"
                )
        return self
