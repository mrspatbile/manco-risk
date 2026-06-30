# UCITS Monitoring

## Absolute VaR Monitoring

### Regulatory Basis

UCITS Directive Article 51 permits two approaches for measuring global exposure:

1. **Commitment approach** (derivative-based, already implemented).
2. **VaR approach** (market risk-based, this module).

This module implements the **absolute VaR approach**.

### Regulatory Threshold

When the absolute VaR approach is used, this module evaluates compliance against a threshold ratio of 20% of NAV. The threshold is defined by:

```python
UCITS_ABSOLUTE_VAR_LIMIT_RATIO = Decimal("0.20")
```

**Recommended methodology** per ESMA Guidelines 10-788:
- Confidence level: 99%
- Holding period: 10 days
- Observation window: 1 year

**VaR convention**: VaR amount is represented as a positive monetary loss.
For example, EUR 1,800,000 VaR on a EUR 10,000,000 NAV = 18% of NAV.

### Compliance Status

| Status | Meaning |
|--------|---------|
| WITHIN_LIMIT | VaR ≤ threshold (compliant) |
| BREACH | VaR > threshold (non-compliant) |

### Example

**Fund NAV**: EUR 10,000,000  
**VaR (99%, 10-day)**: EUR 1,800,000 (18% of NAV)  
**Regulatory Threshold**: `UCITS_ABSOLUTE_VAR_LIMIT_RATIO = 0.20` → EUR 2,000,000  
**Status**: WITHIN_LIMIT

**If VaR = EUR 2,500,000 (25% of NAV)**:  
**Excess**: EUR 500,000 (or 5 percentage points)  
**Status**: BREACH

### Engine Behavior

The `UCITSAbsoluteVaREngine`:

- Accepts a VaR observation (fund, date, NAV, VaR amount, confidence, horizon).
- Calculates VaR ratio from VaR amount and NAV.
- Compares VaR ratio to the regulatory threshold.
- Returns status, threshold, excess, and audit fields.

The engine does not calculate VaR. It consumes pre-calculated observations 
from any VaR methodology (historical, parametric, Monte Carlo, etc.).

### Input and Output

**Input** (`UCITSAbsoluteVaRInput`):
- `fund_id`: Fund identifier
- `valuation_date`: Snapshot date
- `nav`: Net asset value
- `var_amount`: VaR in base currency
- `confidence_level`: VaR confidence level
- `holding_period_days`: VaR holding period

**Output** (`UCITSAbsoluteVaRResult`):
- `status`: WITHIN_LIMIT or BREACH
- `var_ratio`: VaR as fraction of NAV (calculated)
- `threshold_ratio`: Regulatory limit as fraction (0.20)
- `threshold_amount`: Limit in base currency (calculated)
- `excess_amount`: Overage amount (if any, calculated)
- `excess_ratio`: Overage ratio (if any, calculated)
- Audit fields: fund_id, date, confidence level, holding period
