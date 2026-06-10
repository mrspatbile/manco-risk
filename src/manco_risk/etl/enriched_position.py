"""Risk-ready enriched position models for manco-risk.

Responsibilities:
- Define EnrichedPosition: a source position enriched with market data and conversions
- Define RiskReadyPortfolio: a collection of enriched positions with portfolio metadata
- Validate fields according to data conventions (decimals, currencies, weights)
- Provide immutable typed objects for risk calculation consumption

Notes:
- Enriched positions are in-memory objects; not persisted to database.
- All monetary values use Decimal for precision.
- Weights are decimal ratios (0.0 to 1.0), not percentages or strings.
- Currency codes are uppercase (convention from Position ingestion).
- Optional duration field for fixed-income assets only.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class EnrichedPosition(BaseModel):
    """A source position enriched with market data and currency conversion.

    Represents a single holding after enrichment with:
    - Current market price and base-currency valuation
    - Portfolio weight
    - Asset class and duration (if fixed income)

    Fields:
    - fund_id: Fund identifier (immutable link to Fund table)
    - position_snapshot_id: PositionSnapshot identifier (immutable link)
    - position_id: Position identifier (immutable link)
    - isin: Instrument ISIN (immutable)
    - valuation_date: Position valuation date (immutable)
    - quantity: Number of shares/units (can be negative for shorts)
    - market_value: Position value in instrument currency (source fidelity)
    - position_currency: Instrument currency code (e.g., 'USD', 'EUR')
    - asset_class: Asset classification from instrument reference (e.g., 'EQUITY', 'BOND')
    - instrument_currency: Currency of the instrument (matches position_currency)
    - market_value_base_ccy: Position value in fund base currency (enriched)
    - fund_base_currency: Fund base currency for denomination (e.g., 'EUR')
    - weight: Position as decimal ratio of total NAV (0.0 to 1.0)
    - modified_duration: Modified duration in years (optional, bonds only)

    Units and conventions:
    - monetary values (market_value, market_value_base_ccy): Decimal
    - weight: decimal ratio, e.g., 0.05 = 5% of NAV
    - modified_duration: years as Decimal (if present)
    - quantity: can be negative for short positions
    - currency codes: uppercase
    """

    fund_id: int
    position_snapshot_id: int
    position_id: int
    isin: str
    valuation_date: str
    quantity: Decimal
    market_value: Decimal
    position_currency: str
    asset_class: str
    instrument_currency: str
    market_value_base_ccy: Decimal
    fund_base_currency: str
    weight: Decimal
    modified_duration: Optional[Decimal] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("position_currency", "instrument_currency", "fund_base_currency")
    @classmethod
    def validate_currency_uppercase(cls, v: str) -> str:
        """Currency codes must be uppercase."""
        if not v.isupper():
            raise ValueError(f"Currency code must be uppercase, got '{v}'")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: Decimal) -> Decimal:
        """Weight must be non-negative decimal ratio (0.0 to 1.0+)."""
        if v < Decimal("0"):
            raise ValueError(f"Weight must be non-negative, got {v}")
        return v

    @field_validator("market_value_base_ccy")
    @classmethod
    def validate_market_value_base_ccy(cls, v: Decimal) -> Decimal:
        """Market value in base currency must be non-negative."""
        if v < Decimal("0"):
            raise ValueError(f"Market value in base currency must be non-negative, got {v}")
        return v

    @field_validator("modified_duration", mode="before")
    @classmethod
    def validate_duration(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Duration must be positive if present."""
        if v is None:
            return None
        if not isinstance(v, Decimal):
            v = Decimal(str(v))
        if v < Decimal("0"):
            raise ValueError(f"Modified duration must be non-negative, got {v}")
        return v


class RiskReadyPortfolio(BaseModel):
    """A portfolio of enriched positions ready for risk calculation.

    Contains all positions for a fund on a valuation date after enrichment,
    plus portfolio-level metadata needed by risk engines.

    Fields:
    - fund_id: Fund identifier
    - valuation_date: Valuation date for all positions (ISO 8601)
    - fund_base_currency: Fund base currency (uppercase)
    - nav: Fund net asset value (denominator for weights)
    - positions: List of enriched positions

    Invariants:
    - All positions must have the same fund_id, valuation_date, and fund_base_currency
    - nav must be strictly positive
    - positions list may be empty (degenerate case)

    Properties:
    - total_weight: Sum of position weights (should approximate 1.0 for fully invested)
    """

    fund_id: int
    valuation_date: str
    fund_base_currency: str
    nav: Decimal
    positions: list[EnrichedPosition]

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_base_currency")
    @classmethod
    def validate_currency_uppercase(cls, v: str) -> str:
        """Currency code must be uppercase."""
        if not v.isupper():
            raise ValueError(f"Currency code must be uppercase, got '{v}'")
        return v

    @field_validator("nav")
    @classmethod
    def validate_nav(cls, v: Decimal) -> Decimal:
        """NAV must be strictly positive."""
        if v <= Decimal("0"):
            raise ValueError(f"NAV must be strictly positive, got {v}")
        return v

    @field_validator("positions")
    @classmethod
    def validate_positions_consistency(
        cls, v: list[EnrichedPosition], info
    ) -> list[EnrichedPosition]:
        """All positions must match portfolio fund_id, valuation_date, and fund_base_currency."""
        if not v:
            # Empty portfolio is valid (degenerate case)
            return v

        # Access other validated fields via info.data
        fund_id = info.data.get("fund_id")
        valuation_date = info.data.get("valuation_date")
        fund_base_currency = info.data.get("fund_base_currency")

        for idx, position in enumerate(v):
            if position.fund_id != fund_id:
                raise ValueError(
                    f"Position {idx}: fund_id {position.fund_id} does not match "
                    f"portfolio fund_id {fund_id}"
                )
            if position.valuation_date != valuation_date:
                raise ValueError(
                    f"Position {idx}: valuation_date {position.valuation_date} does not match "
                    f"portfolio valuation_date {valuation_date}"
                )
            if position.fund_base_currency != fund_base_currency:
                raise ValueError(
                    f"Position {idx}: fund_base_currency {position.fund_base_currency} does not match "
                    f"portfolio fund_base_currency {fund_base_currency}"
                )

        return v

    @property
    def total_weight(self) -> Decimal:
        """Sum of all position weights.

        Returns
        -------
        Decimal
            Sum of position weights. Should approximate 1.0 for fully invested
            portfolios, but may be less if portfolio has uninvested cash or
            greater if leveraged.
        """
        return sum((position.weight for position in self.positions), Decimal("0"))
