"""UCITS monitoring constants.

Regulatory thresholds and limits for UCITS funds.
"""

from decimal import Decimal

# UCITS Directive Article 51: Absolute VaR monitoring threshold
# Portfolio VaR must not exceed 20% of NAV when using absolute VaR approach
UCITS_ABSOLUTE_VAR_LIMIT_RATIO = Decimal("0.20")

# CESR/ESMA SRRI (Synthetic Risk and Reward Indicator) volatility bands
# Maps annualised volatility ranges to SRRI classes (1-7)
# Per PRIIPs Regulation Commission Delegated Regulation (EU) 2017/653 Annex II
SRRI_VOLATILITY_BANDS = (
    # (lower_bound, upper_bound, srri_class)
    # SRRI 1: < 0.5%
    (Decimal("0.00"), Decimal("0.005"), 1),
    # SRRI 2: 0.5% - < 2%
    (Decimal("0.005"), Decimal("0.02"), 2),
    # SRRI 3: 2% - < 5%
    (Decimal("0.02"), Decimal("0.05"), 3),
    # SRRI 4: 5% - < 10%
    (Decimal("0.05"), Decimal("0.10"), 4),
    # SRRI 5: 10% - < 15%
    (Decimal("0.10"), Decimal("0.15"), 5),
    # SRRI 6: 15% - < 25%
    (Decimal("0.15"), Decimal("0.25"), 6),
    # SRRI 7: >= 25%
    (Decimal("0.25"), Decimal("999.99"), 7),
)

# UCITS Directive Article 51: Maximum direct borrowing limit
# Direct borrowing must not exceed 10% of NAV
UCITS_BORROWING_LIMIT_RATIO = Decimal("0.10")

# UCITS Directive Article 52(1): Single issuer concentration limit
# Exposure to a single issuer must not exceed 10% of NAV
UCITS_ISSUER_CONCENTRATION_LIMIT_RATIO = Decimal("0.10")

# CESR/ESMA Guidelines 10-788: Relative VaR global exposure monitoring
# Fund VaR must not exceed 200% of the reference portfolio VaR (limit ratio = 2.0)
UCITS_RELATIVE_VAR_LIMIT_RATIO = Decimal("2.0")
