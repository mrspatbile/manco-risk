"""UCITS monitoring constants.

Regulatory thresholds and limits for UCITS funds.
"""

from decimal import Decimal

# UCITS Directive Article 51: Absolute VaR monitoring threshold
# Portfolio VaR must not exceed 20% of NAV when using absolute VaR approach
UCITS_ABSOLUTE_VAR_LIMIT_RATIO = Decimal("0.20")
