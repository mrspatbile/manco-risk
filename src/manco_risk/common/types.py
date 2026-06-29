"""Shared types and enumerations."""

from enum import Enum


class AssetClass(str, Enum):
    """Asset classification for instruments.

    Values follow the source-data/database convention (title-case or code-like)
    rather than the uppercase internal labels used by some risk engines.

    Do not change these values without updating ETL/database CSV mappings
    and all asset-class comparisons.

    Note: Some risk engines (equity_stress, fixed_income_stress) use uppercase
    equivalents ("EQUITY", "BOND", "CASH", etc.) internally. These are not
    derived from this enum; they are hardcoded for computational isolation.
    Future refactoring may standardize this.
    """

    EQUITY = "Equity"
    BOND = "Bond"
    FX = "FX"
    INDEX = "Index"
    CASH = "Cash"
    ETF = "ETF"
    LISTED_FUND = "Listed Fund"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
