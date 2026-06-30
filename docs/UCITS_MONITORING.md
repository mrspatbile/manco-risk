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

---

## SRRI (Synthetic Risk and Reward Indicator)

### Purpose

SRRI is a 7-point scale measuring the synthetic risk of a fund based on volatility.
Used in investor communications and regulatory disclosures under PRIIPs.

### Volatility Bands

The engine maps annualised volatility to SRRI class per CESR/ESMA methodology:

| SRRI Class | Volatility Range |
|------------|------------------|
| 1 | < 0.5% |
| 2 | 0.5% - < 2% |
| 3 | 2% - < 5% |
| 4 | 5% - < 10% |
| 5 | 10% - < 15% |
| 6 | 15% - < 25% |
| 7 | ≥ 25% |

### Engine Behavior

The `SRRIEngine`:

- Accepts an annualised volatility observation (fund, date, volatility).
- Matches volatility against SRRI volatility bands.
- Returns SRRI class (1-7).

The engine does not calculate volatility. It consumes pre-calculated observations
from any volatility methodology (historical, parametric, etc.).

### Input and Output

**Input** (`SRRIInput`):
- `fund_id`: Fund identifier
- `valuation_date`: Snapshot date
- `annualised_volatility`: Annualised volatility as decimal (e.g., 0.15 = 15%)

**Output** (`SRRIResult`):
- `srri_class`: SRRI class 1-7 (calculated)
- Audit fields: fund_id, date, annualised volatility (preserved)

### Assumptions

- Volatility is calculated independently and provided as input.
- Volatility represents total fund risk (no concentration on specific risk factors).
- Linear mapping between volatility and SRRI class (no volatility decay, regime shifts, or adaptive scaling).

### Limitations

- Does not account for credit risk, liquidity risk, or counterparty risk independently.
- SRRI reflects historical volatility only; does not forecast future risk.
- All funds with identical volatility receive identical SRRI regardless of asset class or strategy.

---

## Direct Borrowing Limit Monitoring

### Purpose

Monitor fund direct borrowing against the regulatory limit under the UCITS framework.

Direct borrowing refers to explicit loan facilities, not borrowing inferred from positions or derivatives.

### Regulatory Limit

UCITS Directive Article 51 specifies that direct borrowing must not exceed 10% of NAV, defined by:

```python
UCITS_BORROWING_LIMIT_RATIO = Decimal("0.10")
```

### Scope

This engine monitors **direct borrowings only**:
- Loan facilities (term loans, lines of credit)
- Cash borrowing for settlement
- Explicit short-selling funding

This engine does **not** infer borrowing from:
- Position leverage or short positions
- Derivative notional or delta-adjusted exposure
- Securities financing transactions (SFT) implicit leverage

### Compliance Status

| Status | Meaning |
|--------|---------|
| WITHIN_LIMIT | Direct borrowing ≤ 10% of NAV (compliant) |
| BREACH | Direct borrowing > 10% of NAV (non-compliant) |

### Engine Behavior

The `UCITSBorrowingEngine`:

- Accepts a direct borrowing observation (fund, date, NAV, direct borrowing amount).
- Calculates borrowing ratio from direct borrowing amount and NAV.
- Compares borrowing ratio to 10% threshold.
- Returns status, threshold, and excess fields.

The engine does not infer or calculate borrowing. It consumes pre-observed direct borrowing amounts.

### Input and Output

**Input** (`UCITSBorrowingInput`):
- `fund_id`: Fund identifier
- `valuation_date`: Snapshot date
- `nav`: Net asset value
- `direct_borrowing_amount`: Total direct borrowings (positive monetary amount)

**Output** (`UCITSBorrowingResult`):
- `status`: WITHIN_LIMIT or BREACH
- `borrowing_ratio`: Direct borrowing as fraction of NAV (calculated)
- `limit_ratio`: Regulatory limit as fraction (0.10)
- `limit_amount`: Limit in base currency (calculated)
- `excess_amount`: Overage amount (if any, calculated)
- `excess_ratio`: Overage ratio (if any, calculated)
- Audit fields: fund_id, date, NAV, direct borrowing amount (preserved)

### Assumptions

- Direct borrowing is reported accurately and completely.
- Borrowing includes all explicit loan facilities and cash borrowing.
- Borrowing does not include implicit leverage from positions or derivatives.

### Limitations

- Does not monitor inferred borrowing from derivative notional or SFT leverage.
- Does not distinguish between different types of borrowing (term, revolving, repo).
- Does not account for borrowing costs or collateral requirements.
- Assumes NAV is current and accurate at observation time.
