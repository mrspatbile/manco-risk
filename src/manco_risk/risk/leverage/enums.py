"""Leverage methodology enums.

Defines leverage methods, exposure sources, and exposure treatment classifications.
Leverage is source-first (where does exposure come from), then method-first (how to aggregate).
"""

from enum import Enum


class LeverageMethod(str, Enum):
    """Leverage calculation method per regulatory framework.

    AIFMD_GROSS: Gross method from EU Regulation 231/2013 Article 7.
    AIFMD_COMMITMENT: Commitment method from EU Regulation 231/2013 Article 8.
    UCITS_COMMITMENT: UCITS commitment-approach global exposure (future).
    UCITS_VAR_GLOBAL_EXPOSURE: UCITS VaR-based global exposure (future).
    """

    AIFMD_GROSS = "AIFMD_GROSS"
    AIFMD_COMMITMENT = "AIFMD_COMMITMENT"
    UCITS_COMMITMENT = "UCITS_COMMITMENT"
    UCITS_VAR_GLOBAL_EXPOSURE = "UCITS_VAR_GLOBAL_EXPOSURE"


class LeverageSource(str, Enum):
    """Exposure sources for leverage calculation.

    Classifies where leverage exposure originates before aggregation by method.

    Physical instruments: Equities, bonds, ETFs, listed funds.
    Cash: Cash and cash equivalents; important for exclusions and borrowing tracking.
    Borrowing: Direct cash/securities borrowing.
    Reinvested borrowing: Borrowed cash that has been invested.
    SFT: Securities financing transactions (repo, reverse repo, securities lending).
    Derivatives: Exposure from derivatives (futures, options, swaps).
    Embedded: Leverage embedded in structured instruments.
    Look-through: Fund holdings requiring look-through aggregation.
    Other: Explicit fallback.
    """

    PHYSICAL_INSTRUMENT = "PHYSICAL_INSTRUMENT"
    CASH_AND_CASH_EQUIVALENT = "CASH_AND_CASH_EQUIVALENT"
    DIRECT_BORROWING = "DIRECT_BORROWING"
    REINVESTED_BORROWING = "REINVESTED_BORROWING"
    SFT_REPO = "SFT_REPO"
    SFT_REVERSE_REPO = "SFT_REVERSE_REPO"
    SECURITIES_LENDING = "SECURITIES_LENDING"
    DERIVATIVE = "DERIVATIVE"
    EMBEDDED_DERIVATIVE = "EMBEDDED_DERIVATIVE"
    FUND_LOOK_THROUGH = "FUND_LOOK_THROUGH"
    CONTROLLED_STRUCTURE = "CONTROLLED_STRUCTURE"
    OTHER = "OTHER"


class ExposureTreatment(str, Enum):
    """Treatment status of an exposure in leverage calculation.

    INCLUDED: Exposure is included in the relevant source base.
    EXCLUDED: Exposure is explicitly excluded with stated reason.
    UNSUPPORTED: Source/asset exists but is not supported yet.
    PENDING_METHOD_RULE: Source identified, but final treatment depends on later
                          gross/commitment/UCITS rules.
    """

    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    UNSUPPORTED = "UNSUPPORTED"
    PENDING_METHOD_RULE = "PENDING_METHOD_RULE"
