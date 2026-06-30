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

---

## Single-Issuer Concentration Monitoring

### Purpose

Monitor fund exposure to individual issuers against regulatory limits under the UCITS framework.

This engine evaluates **single-issuer concentration only**, not aggregated issuer groups.

### Regulatory Basis

UCITS Directive Article 52(1): Single Issuer Limit  
Exposure to a single issuer must not exceed 10% of NAV.

**Related Article 52 rules (out of scope for this slice):**
- 20% limit for groups of issuers with a common control (future slice)
- 20% limit for deposits (future slice)
- 10% limit for OTC counterparty exposure (future slice)
- Exemptions for government securities and index replication (deliberately out of scope)

### Scope

This engine monitors **single issuers only**:
- Individual issuer exposure by LEI, ticker, or identifier
- Bonds, equities, derivatives notional (if pre-computed as exposure amount)

This engine does **NOT**:
- Aggregate issuer exposure from positions
- Perform group issuer logic or look-through
- Apply exemptions (government securities, index replication, etc.) — exemptions are deliberately out of scope for this slice
- Calculate issuer exposure
- Infer exposure from derivatives or SFT leverage
- Perform portfolio aggregation or backtesting

### Compliance Status

| Status | Meaning |
|--------|---------|
| WITHIN_LIMIT | Issuer exposure ≤ 10% of NAV (compliant) |
| BREACH | Issuer exposure > 10% of NAV (non-compliant) |

### Engine Behavior

The `UCITSConcentrationEngine`:

- Accepts a single-issuer exposure observation (fund, date, NAV, issuer, exposure amount).
- Calculates exposure ratio from exposure amount and NAV.
- Compares exposure ratio to 10% threshold.
- Returns status, threshold, and excess fields.

The engine does not aggregate or calculate issuer exposure. It consumes pre-computed single-issuer observations.

### Input and Output

**Input** (`UCITSConcentrationInput`):
- `fund_id`: Fund identifier
- `valuation_date`: Snapshot date
- `nav`: Net asset value
- `issuer_id`: Issuer identifier (LEI or code)
- `issuer_name`: Issuer name for audit (optional)
- `issuer_exposure_amount`: Total exposure to this issuer (positive monetary amount)

**Output** (`UCITSConcentrationResult`):
- `status`: WITHIN_LIMIT or BREACH
- `exposure_ratio`: Issuer exposure as fraction of NAV (calculated)
- `limit_ratio`: Regulatory limit as fraction (0.10)
- `limit_amount`: Limit in base currency (calculated)
- `excess_amount`: Overage amount (if any, calculated)
- `excess_ratio`: Overage ratio (if any, calculated)
- Audit fields: fund_id, issuer_id, issuer_name, valuation_date, NAV, exposure amount (preserved)

### Assumptions

- Issuer exposure is pre-computed and provided as input.
- Exposure represents total fund holding in that issuer across all instruments.
- Issuer exposure is accurate and complete.

### Limitations

- Does not aggregate group issuer exposures (20% rule for groups is separate)
- Does not handle exemptions (government securities, index replication, etc.)
- Does not perform look-through for collective investments
- Does not monitor OTC counterparty or deposit limits separately
- Assumes NAV is current and accurate at observation time
- Does not distinguish between different types of issuer (financial, non-financial, sovereign)

---

## Relative VaR Monitoring

### Purpose

Monitor fund VaR against a reference portfolio (benchmark) VaR under the UCITS framework.

The relative VaR approach allows fund managers to manage risk relative to a chosen reference index or strategy.

### Regulatory Basis

CESR/ESMA Guidelines 10-788: Relative VaR Global Exposure Monitoring  
Fund VaR must not exceed 200% of reference portfolio VaR (limit ratio = 2.0x).

This is one of three ESMA-approved global exposure methods for UCITS funds:
1. **Commitment approach** (derivative-based, already implemented)
2. **Absolute VaR approach** (20% of NAV, already implemented)
3. **Relative VaR approach** (fund VaR up to 2x benchmark VaR, this slice)

### Scope

This engine monitors **relative VaR only**:
- Fund VaR vs. reference portfolio VaR
- Pre-computed VaR observations (any methodology)

This engine does **NOT**:
- Calculate VaR (consumes pre-calculated observations)
- Construct or select reference portfolios/benchmarks
- Perform VaR simulation or backtesting
- Fetch market data
- Handle fund selection or portfolio construction

### Compliance Status

| Status | Meaning |
|--------|---------|
| WITHIN_LIMIT | Fund VaR ≤ 200% of Reference Portfolio VaR (compliant) |
| BREACH | Fund VaR > 200% of Reference Portfolio VaR (non-compliant) |

### Engine Behavior

The `UCITSRelativeVaREngine`:

- Accepts VaR observations (fund, date, fund VaR, reference portfolio VaR, confidence, horizon).
- Calculates relative VaR ratio from fund VaR and reference portfolio VaR.
- Compares ratio to 1.0x threshold.
- Returns status, ratio, and excess fields.

The engine does not calculate or construct VaR/benchmarks. It consumes pre-computed observations.

### Input and Output

**Input** (`UCITSRelativeVaRInput`):
- `fund_id`: Fund identifier
- `valuation_date`: Snapshot date
- `fund_var`: Fund VaR amount (non-negative)
- `reference_portfolio_var`: Reference portfolio/benchmark VaR amount (positive)
- `confidence_level`: VaR confidence level (audit)
- `holding_period_days`: VaR holding period (audit)

**Output** (`UCITSRelativeVaRResult`):
- `status`: WITHIN_LIMIT or BREACH
- `relative_var_ratio`: Fund VaR as multiple of reference VaR (calculated)
- `limit_ratio`: Regulatory limit as multiple (2.0 = fund VaR must not exceed 2× reference)
- `excess_ratio`: Excess as multiple above reference (calculated)
- Audit fields: fund_id, date, fund VaR, reference VaR, confidence level, holding period (preserved)

### Assumptions

- Fund VaR and reference portfolio VaR are pre-computed using consistent methodology.
- Both VaR observations use the same confidence level and holding period.
- Reference portfolio is appropriate for the fund's strategy.
- VaR calculations are accurate and complete.

### Limitations

- Does not calculate or simulate VaR
- Does not construct or validate reference portfolios
- Does not handle benchmark selection
- Does not distinguish between different VaR methodologies
- Assumes pre-computed VaR observations are correct
- Does not monitor other global exposure methods (commitment approach, absolute VaR)
- Assumes both VaR values use consistent parameters (confidence level, holding period)
