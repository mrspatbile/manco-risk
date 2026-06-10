"""Shared types and enumerations."""

from enum import Enum


class AssetClass(str, Enum):
    """Asset classification for instruments."""

    EQUITY = "Equity"
    BOND = "Bond"
    FX = "FX"
    INDEX = "Index"
    CASH = "Cash"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
