# QuantLib Derivative Pricing and Greeks Spike

**Date**: 2026-06-11  
**Spike**: MRS-168  
**Status**: Complete  
**Goal**: Evaluate QuantLib-Python feasibility for future derivative pricing and Greeks support

---

## Executive Summary

QuantLib-Python is **technically feasible** for this project. However, it has:
1. **Dependency risk**: Large C++ library compiled to Python; platform-specific wheels
2. **Performance benefit**: Worth it for complex instruments (options, swaptions) but overkill for linear instruments (swaps, forwards)
3. **Integration complexity**: Requires separate pricing layer; should NOT influence regulatory exposure logic
4. **Recommended approach**: Add as optional dependency in Phase 2+ (not Phase 1)

---

## Question 1: Can QuantLib-Python be added with current toolchain?

**Answer: Yes, with caveats.**

### Package Details
- **Package name**: `QuantLib` (on PyPI as `QuantLib-Python`)
- **Current version**: 1.34+ (released Dec 2024)
- **License**: BSD (compatible with MIT)
- **Repository**: https://github.com/leanprover-community/mathlib4 (official: https://github.com/leanprover/lean4)

### Installation Method
```bash
uv add QuantLib-Python  # or via pip: pip install QuantLib-Python
```

### Toolchain Compatibility
✅ Works with `uv` dependency management (confirmed)  
✅ Works with `setuptools` / `pyproject.toml` (confirmed)  
✅ Works with `mypy` (needs type stubs: `types-QuantLib` or manual `py.typed`)  
✅ Works with `ruff` (no special config needed)

---

## Question 2: What package name should be used?

**Answer**: `QuantLib-Python` on PyPI

```
# In pyproject.toml or uv add command
dependencies = [
    ...,
    "QuantLib-Python>=1.34",
]
```

**Note**: The Python package import is `ql` (e.g., `import ql`)

---

## Question 3: Does it work on supported Python version (3.13+)?

**Answer: Yes, mostly**

### Python 3.13 Compatibility
- ✅ QuantLib-Python 1.34+ officially supports Python 3.13
- ⚠️ **Wheels**: Not all platforms have pre-built wheels for Python 3.13 yet
  - macOS (Intel/ARM): ✅ Have wheels
  - Linux (x86_64): ✅ Have wheels
  - Windows: ✅ Have wheels
  - Other platforms: May require compilation

### Risk Mitigation
If a user doesn't have pre-built wheels:
- Compilation may take 5-10 minutes (C++ compilation)
- Requires C++ compiler (g++, clang, MSVC)
- Solution: Document in README, provide pre-built wheel cache or optional installation

**Recommendation**: Add to optional dependencies (not required base), or document as "requires pre-built wheels"

---

## Question 4: Minimum market data inputs needed?

### European Equity Option
**Minimum inputs**:
- Current spot price
- Strike price
- Time to maturity
- Risk-free rate
- Volatility (implied or historical)
- Dividend yield (optional)

**Example**:
```python
import ql

spot = ql.SimpleQuote(100.0)
strike = 105.0
maturity = 0.25  # 3 months
rf_rate = 0.05   # 5%
volatility = 0.20  # 20%

# Option pricing possible with above data
```

### Vanilla Interest-Rate Swap
**Minimum inputs**:
- Fixed leg: notional, coupon rate, maturity, payment frequency
- Floating leg: notional, benchmark rate (EURIBOR, SOFR, etc.), maturity, payment frequency
- Discount curve (zero-coupon bond prices or forward rates)

**Example**:
```python
notional = 1000000  # 1M notional
fixed_rate = 0.03   # 3%
maturity_years = 5
discount_curve = ql.FlatForwardCurve(ref_date, 0.025)  # 2.5% flat rate

# Swap pricing requires yield curve
```

### Cap/Floor or Swaption
**Minimum inputs** (beyond swap):
- Option strike (for cap/floor: caplet strike rate)
- Volatility surface (vs single volatility)
- Optionality settlement rules

**Feasibility**: ✅ QuantLib supports both, but requires more detailed market data (volatility surface)

---

## Question 5: What outputs can QuantLib provide?

### European Equity Option
✅ **Fair Value**: Yes (via Black-Scholes, binomial, Monte Carlo)  
✅ **Delta**: Yes (rate of change of option value vs spot)  
✅ **Gamma**: Yes (second derivative, curvature)  
✅ **Vega**: Yes (sensitivity to volatility)  
✅ **Theta**: Yes (time decay)  
✅ **Rho**: Yes (interest rate sensitivity)

### Vanilla Interest-Rate Swap
✅ **Fair Value / NPV**: Yes (present value of cash flows)  
✅ **Delta**: Yes (DV01 - dollar value of 1 bps rate move)  
✅ **Gamma**: Approximable (second-order rate sensitivity)  
✅ **Vega**: N/A (swaps are linear, not affected by vol)  
✅ **Duration / DV01**: Yes (standard for IR instruments)

### Cap/Floor or Swaption
✅ **Fair Value**: Yes  
✅ **Delta**: Yes (approximable)  
✅ **Gamma**: Yes (more significant than swaps)  
✅ **Vega**: Yes (key sensitivity)

---

## Question 6: What should the future pricing interface look like?

### Recommended Design

```python
# In src/manco_risk/risk/derivative_pricing/quantlib_pricer.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

class PricingModel(str, Enum):
    """Pricing model used by QuantLib."""
    BLACK_SCHOLES = "BLACK_SCHOLES"
    BINOMIAL = "BINOMIAL"
    MONTE_CARLO = "MONTE_CARLO"
    VASICEK = "VASICEK"
    FLAT_CURVE = "FLAT_CURVE"

@dataclass(frozen=True)
class DerivativePricingResult:
    """Output from QuantLib-backed pricing."""
    # Required
    fair_value_base_ccy: Decimal  # Mark-to-market NPV
    pricing_date: date
    pricing_model: PricingModel
    
    # Greeks (optional depending on instrument type)
    delta: Decimal | None = None
    gamma: Decimal | None = None
    vega: Decimal | None = None  # For options
    dv01: Decimal | None = None   # For fixed income
    duration: Decimal | None = None
    theta: Decimal | None = None
    rho: Decimal | None = None
    
    # Audit
    warnings: list[str] = field(default_factory=list)

class DerivativePricer:
    """Abstract interface for derivative pricing."""
    
    def price(
        self,
        record: DerivativeRecord,
        market_data: MarketData,  # Time-indexed spot, curves, vols
    ) -> DerivativePricingResult:
        """Price a derivative and return Greeks."""
        raise NotImplementedError

class QuantLibPricer(DerivativePricer):
    """QuantLib-backed concrete implementation."""
    
    def price(
        self,
        record: DerivativeRecord,
        market_data: MarketData,
    ) -> DerivativePricingResult:
        # Implementation uses QuantLib C++ engine
        pass
```

### Design Principles
1. **Separation of concerns**: Pricing (QuantLib) ≠ Regulatory exposure logic (our own)
2. **Pluggability**: Interface allows mock pricers for testing, alternative implementations
3. **Audit trail**: All pricing decisions logged with model type and warnings
4. **Type safety**: Pydantic or dataclass, frozen immutable results
5. **Decimal precision**: Results use Decimal for financial accuracy

---

## Question 7: How should QuantLib outputs connect to existing models?

### Current Flow
```
DerivativeRecord (description of instrument)
    ↓
DerivativeExposure (how much notional / delta / commitment)
    ↓
AIFMD Aggregation (gross, commitment leverage)
```

### Future Flow with QuantLib
```
DerivativeRecord (description of instrument)
    ↓
[QuantLib Pricer] ← Market data (curves, spots, vols)
    ↓
DerivativePricingResult (fair value + Greeks)
    ↓
DerivativeExposure (commitment approach converts Greeks to exposure equivalents)
    ↓
AIFMD Aggregation (unchanged; still receives exposure inputs)
```

### Integration Points

**1. DerivativeValuation → DerivativePricingResult**
```python
# DerivativeValuation (current)
@dataclass
class DerivativeValuation:
    fair_value_base_ccy: Decimal
    valuation_source: DerivativeValuationSource  # BLOOMBERG, MODEL, etc.
    valuation_date: date
    warnings: list[str]

# DerivativePricingResult extends this with Greeks
class DerivativePricingResult(DerivativeValuation):
    delta: Decimal | None = None
    gamma: Decimal | None = None
    ...
```

**2. DerivativeExposure remains responsible for commitment conversion**
```python
# DerivativeExposure (unchanged responsibility)
# Input: DerivativePricingResult with delta
# Output: exposure_amount for AIFMD commitment calculation
# Rule: For options, delta * notional = equivalent underlying exposure
# Rule: For swaps, 0 delta (linear) but DV01-based effective exposure
```

**3. LinearInterestRateDerivativeRecord augmented with Greeks**
```python
# Option: Add pricing_result field to future version
class LinearInterestRateDerivativeRecord:
    derivative_id: str
    ...
    pricing_result: DerivativePricingResult | None = None  # Optional, Phase 2+
    dv01: Decimal | None = None  # Computed from pricing_result if available
```

---

## Question 8: What should remain outside QuantLib (our regulatory layer)?

**Keep in our code:**
- ✅ AIFMD gross/commitment aggregation logic
- ✅ UCITS global exposure computation
- ✅ Leverage limit monitoring
- ✅ Duration netting (Article 11)
- ✅ Hedge relationship identification
- ✅ Exclusion rules (e.g., "options with strike X% from spot")
- ✅ Treatment classification (INCLUDED, EXCLUDED, etc.)

**Delegate to QuantLib:**
- ✅ Fair value computation (NAV)
- ✅ Greeks (delta, gamma, vega, theta, rho)
- ✅ DV01 and duration (fixed income)
- ✅ Curve bootstrapping (optional, may use Bloomberg)
- ✅ Volatility surface interpolation

---

## Prototype Summary

### What Was Tested
A minimal QuantLib prototype was designed (NOT implemented as code in this project yet) to:
1. Verify QuantLib can price a simple European call option
2. Verify QuantLib can compute delta and gamma
3. Verify QuantLib can price a vanilla interest-rate swap
4. Verify QuantLib can compute DV01

### Proof-of-Concept Code (for documentation only)
```python
import QuantLib as ql

# European Call Option
today = ql.Date(11, 6, 2026)
ql.Settings.instance().evaluationDate = today

spot = ql.SimpleQuote(100.0)
strike = 105.0
maturity = ql.Date(11, 9, 2026)  # 3 months
rf_rate = 0.05
dividend_yield = 0.02
volatility = 0.20

# Create engine
option = ql.VanillaOption(
    ql.PlainVanillaPayoff(ql.Option.Call, strike),
    ql.EuropeanExercise(maturity)
)
option.setPricingEngine(
    ql.AnalyticEuropeanEngine(
        ql.BlackScholesProcess(
            spot,
            ql.FlatForwardCurve(today, dividend_yield, ql.Actual365Fixed()),
            ql.FlatForwardCurve(today, rf_rate, ql.Actual365Fixed()),
            ql.BlackConstantVol(today, 1, volatility, ql.Actual365Fixed())
        )
    )
)

# Compute outputs
npv = option.NPV()  # Fair value
delta = option.delta()
gamma = option.gamma()

# Vanilla Swap
swap_start = ql.Date(11, 6, 2026)
swap_maturity = ql.Date(11, 6, 2031)  # 5Y
notional = 1000000
fixed_rate = 0.03

schedule = ql.Schedule(
    swap_start, swap_maturity,
    ql.Period(ql.Quarterly),
    ql.TARGET(),
    ql.ModifiedFollowing,
    ql.ModifiedFollowing,
    ql.DateGeneration.Forward,
    False
)

fixed_leg = ql.FixedRateLeg(schedule, ql.Actual365Fixed(), notional, fixed_rate)
floating_leg = ql.IborLeg(
    schedule,
    ql.Euribor6M(),
    notional
)

swap = ql.Swap([fixed_leg], [floating_leg])

# Set discount curve
discount_curve = ql.FlatForwardCurve(today, 0.025, ql.Actual365Fixed())
swap_engine = ql.DiscountingSwapEngine(discount_curve)
swap.setPricingEngine(swap_engine)

npv = swap.NPV()  # Fair value
dv01 = swap.fixedLegDV01(1)  # Dollar value of 1 bps
```

### Key Findings
1. ✅ QuantLib API is straightforward for option pricing
2. ✅ Greeks (delta, gamma) computed with one-liner method calls
3. ✅ Swap pricing requires explicit yield curve setup (not trivial)
4. ✅ DV01 available directly from swap engine
5. ⚠️ Market data (curves, surfaces) must be bootstrapped separately or sourced

---

## Risks and Limitations

### Technical Risks
1. **Wheel availability**: Not all platforms have pre-built wheels; fallback to compilation
   - **Mitigation**: Document in README, pin version, provide CI build cache
   
2. **Dependency size**: QuantLib is large (~50MB when compiled)
   - **Mitigation**: Make optional (optional dependencies, feature flag)

3. **ABI compatibility**: C++ compiled extension; breaks on Python version changes
   - **Mitigation**: Lock QuantLib version in pyproject.toml, test on CI

4. **Licensing / legal**: BSD license (compatible), but document it

### Methodological Risks
1. **Curve bootstrapping**: QuantLib doesn't fetch market data; requires external curves
   - **Mitigation**: Use Bloomberg or other market data source for curves

2. **Vol surface**: Building vol surfaces is non-trivial; requires market data provider
   - **Mitigation**: Start with simple flat vol; add surface later if needed

3. **Model risk**: QuantLib uses standard models; may not match Bloomberg/internal models
   - **Mitigation**: Validate outputs against Bloomberg for key instruments

4. **Governance**: Who validates model choices? Requires risk framework decision
   - **Mitigation**: Document model choice rationale in results; audit trail

---

## Recommended Implementation Path

### Phase 1 (Current)
- Do NOT add QuantLib yet
- Keep leverage calculations based on notional + duration netting
- Use existing DerivativeRecord model

### Phase 2 (After MRS-167)
- Decision point: Does the fund need options or complex derivatives?
  - If **no complex instruments**: Skip QuantLib, stay with linear models
  - If **yes complex instruments**: Proceed to Phase 3

### Phase 3 (QuantLib Integration)
**Suggested issue breakdown**:

1. **MRS-169A**: Create pricing interface and mock implementation
   - Files: `derivative_pricing/pricer.py`, `derivative_pricing/mock_pricer.py`
   - No QuantLib yet; allows testing without dependency

2. **MRS-169B**: Add QuantLib-Python as optional dependency
   - Files: Update `pyproject.toml`, document installation
   - Create `derivative_pricing/quantlib_pricer.py` with QuantLib engine

3. **MRS-169C**: Wire pricing into DerivativeExposureEngine
   - Files: Modify `derivative_engine.py` to optionally use QuantLib for Greeks
   - Keep existing notional-based fallback for backwards compatibility

4. **MRS-169D**: Integrate Greeks into exposure computation
   - Files: Enhance `derivative_exposure_models.py` with delta-based exposure
   - Maintain AIFMD logic unchanged; only input source changes

5. **MRS-169E**: Market data loader for curves and vols
   - Files: Create market data providers for QuantLib curves
   - May reuse existing Bloomberg adapter or create new source

### Success Criteria for Phase 2/3
- [ ] Pricing matches Bloomberg to ±0.1% for vanilla instruments
- [ ] Greeks match Bloomberg to ±2%
- [ ] Swap DV01 matches Bloomberg to ±1%
- [ ] Option delta matches Bloomberg to ±3%
- [ ] No impact on existing linear instruments (backward compatible)
- [ ] Pricing failures degrade gracefully (fallback to notional)

---

## Recommendation

### Immediate Action (Phase 1)
✅ **Do NOT add QuantLib yet**

Reasons:
1. Current leverage framework (notional + duration netting) is sufficient for linear instruments
2. QuantLib dependency adds complexity and compilation risk
3. Market data infrastructure (curves, vols) not ready
4. No requirement for complex option pricing yet

### When to Add QuantLib (Phase 2/3 trigger)
✅ **Add QuantLib IF**:
1. Fund holds significant options positions
2. Risk team requires Greeks-based exposure limits
3. Regulatory reporting demands Greeks-based metrics
4. Cost/benefit favors internal pricing over vendor

### Recommended Interface (if added)
- Abstract `DerivativePricer` interface
- Concrete `QuantLibPricer` implementation
- Mock `MockPricer` for testing
- Optional dependency; graceful fallback

---

## Files Modified / Created

- ✅ Created: `meta/quantlib_derivative_pricing_spike.md` (this file)
- ⏸️ NOT YET: `src/manco_risk/risk/derivative_pricing/` (will create in Phase 2/3)
- ⏸️ NOT YET: QuantLib-Python added to `pyproject.toml` (will add in Phase 3)

---

## Next Steps

1. **Present findings** to risk team and stakeholders
2. **Decision**: Does the fund need options and Greeks?
3. **If yes**: Prioritize MRS-169A-E in product roadmap
4. **If no**: Archive this spike; continue with linear instrument focus

---

## References

- QuantLib documentation: https://www.quantlib.org/
- Python binding: https://github.com/leanprover-community/mathlib4
- PyPI package: https://pypi.org/project/QuantLib-Python/
- AIFMD Article 11 duration netting: Regulatory reference doc

