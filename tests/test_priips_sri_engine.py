"""Tests for PRIIPs SRI engine.

Tests the SRIEngine against the regulatory combination table from
Commission Delegated Regulation (EU) 2017/653 Annex II.
"""

from datetime import date

import pytest

from manco_risk.risk.priips import (
    CRM_DEFAULT_CLASS,
    CRM_MAX_CLASS,
    CRM_MIN_CLASS,
    MRM_MAX_CLASS,
    MRM_MIN_CLASS,
    SRI_COMBINATION_TABLE,
    SRI_MAX_CLASS,
    SRI_MIN_CLASS,
    SRIEngine,
    SRIInput,
    SRIResult,
)


class TestSRIEngineRegulatoryTable:
    """Test SRIEngine against the regulatory combination table."""

    def test_sri_cr1_mr1_equals_1(self):
        """CR1 + MR1 → SRI 1 (baseline, no uplift)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=1,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 1

    def test_sri_cr1_mr7_equals_7(self):
        """CR1 + MR7 → SRI 7 (max, no credit uplift)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=7,
            crm_class=1,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 7

    def test_sri_cr2_mr1_equals_1(self):
        """CR2 + MR1 → SRI 1 (CR2 same as CR1)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=2,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 1

    def test_sri_cr2_mr7_equals_7(self):
        """CR2 + MR7 → SRI 7 (CR2 same as CR1)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=7,
            crm_class=2,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 7

    def test_sri_cr3_mr1_equals_3(self):
        """CR3 + MR1 → SRI 3 (CR3 uplift from 1 to 3)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=3,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 3

    def test_sri_cr3_mr3_equals_3(self):
        """CR3 + MR3 → SRI 3 (CR3 keeps at 3)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=3,
            crm_class=3,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 3

    def test_sri_cr3_mr4_equals_4(self):
        """CR3 + MR4 → SRI 4 (MR above CR3 range)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=4,
            crm_class=3,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 4

    def test_sri_cr4_mr1_equals_5(self):
        """CR4 + MR1 → SRI 5 (CR4 uplift from 1 to 5)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=4,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 5

    def test_sri_cr5_mr1_equals_5(self):
        """CR5 + MR1 → SRI 5 (CR5 same as CR4)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=5,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 5

    def test_sri_cr6_mr1_equals_6(self):
        """CR6 + MR1 → SRI 6 (CR6 uplift from 1 to 6)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=6,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 6

    def test_sri_cr6_mr7_equals_7(self):
        """CR6 + MR7 → SRI 7 (max)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=7,
            crm_class=6,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 7


class TestCRMNormalization:
    """Test CRM normalization when None (not applicable)."""

    def test_crm_none_normalizes_to_default(self):
        """CRM=None normalizes to CRM_DEFAULT_CLASS (1) in result."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=5,
            crm_class=None,
        )
        result = SRIEngine.calculate(input_data)
        assert result.crm_class == CRM_DEFAULT_CLASS
        assert result.crm_class == 1

    def test_crm_none_mr5_equals_5(self):
        """CRM=None + MR5 → SRI 5 (normalized to CR1 + MR5 = 5)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=5,
            crm_class=None,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 5

    def test_crm_none_mr1_equals_1(self):
        """CRM=None + MR1 → SRI 1 (normalized to CR1 + MR1 = 1)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=None,
        )
        result = SRIEngine.calculate(input_data)
        assert result.sri_class == 1


class TestResultImmutability:
    """Test that SRIResult is immutable."""

    def test_result_is_frozen(self):
        """SRIResult cannot be mutated after creation."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=3,
            crm_class=2,
        )
        result = SRIEngine.calculate(input_data)

        with pytest.raises(Exception):  # Pydantic frozen models raise ValidationError
            result.sri_class = 5

    def test_result_is_frozen_product_id(self):
        """SRIResult product_id cannot be mutated."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=3,
            crm_class=2,
        )
        result = SRIEngine.calculate(input_data)

        with pytest.raises(Exception):
            result.product_id = "NEW_PRODUCT"


class TestInputValidation:
    """Test input validation."""

    def test_product_id_empty_string_rejected(self):
        """Empty product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            SRIInput(
                product_id="",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=1,
            )

    def test_product_id_whitespace_only_rejected(self):
        """Whitespace-only product_id is rejected."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            SRIInput(
                product_id="   ",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=1,
            )

    def test_mrm_class_below_min_rejected(self):
        """MRM class < 1 is rejected."""
        with pytest.raises(ValueError, match="mrm_class must be in"):
            SRIInput(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=0,
                crm_class=1,
            )

    def test_mrm_class_above_max_rejected(self):
        """MRM class > 7 is rejected."""
        with pytest.raises(ValueError, match="mrm_class must be in"):
            SRIInput(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=8,
                crm_class=1,
            )

    def test_crm_class_below_min_rejected(self):
        """CRM class < 1 is rejected."""
        with pytest.raises(ValueError, match="crm_class must be in"):
            SRIInput(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=0,
            )

    def test_crm_class_above_max_rejected(self):
        """CRM class > 6 is rejected."""
        with pytest.raises(ValueError, match="crm_class must be in"):
            SRIInput(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=7,
            )

    def test_crm_class_none_accepted(self):
        """CRM class = None (not applicable) is accepted."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=1,
            crm_class=None,
        )
        assert input_data.crm_class is None


class TestResultValidation:
    """Test result defensive validation."""

    def test_result_sri_class_below_min_rejected(self):
        """SRI class < 1 rejected by defensive validator."""
        with pytest.raises(ValueError, match="sri_class must be in"):
            SRIResult(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=1,
                sri_class=0,
            )

    def test_result_sri_class_above_max_rejected(self):
        """SRI class > 7 rejected by defensive validator."""
        with pytest.raises(ValueError, match="sri_class must be in"):
            SRIResult(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=1,
                sri_class=8,
            )

    def test_result_mrm_class_invalid_rejected(self):
        """Invalid MRM class rejected by defensive validator."""
        with pytest.raises(ValueError, match="mrm_class must be in"):
            SRIResult(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=8,
                crm_class=1,
                sri_class=7,
            )

    def test_result_crm_class_invalid_rejected(self):
        """Invalid CRM class rejected by defensive validator."""
        with pytest.raises(ValueError, match="crm_class must be in"):
            SRIResult(
                product_id="TEST_PRODUCT",
                valuation_date=date(2026, 6, 30),
                mrm_class=1,
                crm_class=7,
                sri_class=1,
            )


class TestDeterminism:
    """Test engine determinism."""

    def test_same_input_produces_same_output(self):
        """Same input always produces same output (deterministic)."""
        input_data = SRIInput(
            product_id="TEST_PRODUCT",
            valuation_date=date(2026, 6, 30),
            mrm_class=4,
            crm_class=3,
        )
        result1 = SRIEngine.calculate(input_data)
        result2 = SRIEngine.calculate(input_data)

        assert result1.sri_class == result2.sri_class
        assert result1.crm_class == result2.crm_class
        assert result1.product_id == result2.product_id
        assert result1.valuation_date == result2.valuation_date


class TestRegulatoryTableCompleteness:
    """Test that engine handles all valid class combinations."""

    def test_all_valid_mrm_crm_combinations(self):
        """Engine handles all valid MRM × CRM combinations."""
        for crm in range(CRM_MIN_CLASS, CRM_MAX_CLASS + 1):
            for mrm in range(MRM_MIN_CLASS, MRM_MAX_CLASS + 1):
                input_data = SRIInput(
                    product_id=f"TEST_CR{crm}_MR{mrm}",
                    valuation_date=date(2026, 6, 30),
                    mrm_class=mrm,
                    crm_class=crm,
                )
                result = SRIEngine.calculate(input_data)

                # Verify result is in valid range
                assert SRI_MIN_CLASS <= result.sri_class <= SRI_MAX_CLASS
                # Verify result matches table
                expected_sri = SRI_COMBINATION_TABLE[crm][mrm]
                assert result.sri_class == expected_sri
