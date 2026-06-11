"""Tests for derivative leverage exposure engine.

Validates derivative valuation and exposure models, and exposure calculation.
"""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.leverage import (
    ExposureTreatment,
    LeverageSource,
)
from manco_risk.risk.leverage.derivative_engine import DerivativeExposureEngine
from manco_risk.risk.leverage.derivative_models import (
    DerivativeExposure,
    DerivativeExposureSource,
    DerivativePayoffType,
    DerivativeRecord,
    DerivativeType,
    DerivativeValuation,
    DerivativeValuationSource,
)


class TestDerivativeTypeEnum:
    """Test DerivativeType enum."""

    def test_derivative_type_values_exist(self):
        """All required derivative types are defined."""
        assert DerivativeType.FUTURE.value == "FUTURE"
        assert DerivativeType.FORWARD.value == "FORWARD"
        assert DerivativeType.OPTION.value == "OPTION"
        assert DerivativeType.SWAP.value == "SWAP"
        assert DerivativeType.FX_FORWARD.value == "FX_FORWARD"
        assert DerivativeType.CFD.value == "CFD"
        assert DerivativeType.WARRANT.value == "WARRANT"
        assert DerivativeType.OTHER.value == "OTHER"

    def test_derivative_type_count(self):
        """All expected derivative types are present."""
        assert len(list(DerivativeType)) == 8


class TestDerivativePayoffTypeEnum:
    """Test DerivativePayoffType enum."""

    def test_payoff_type_values_exist(self):
        """All required payoff types are defined."""
        assert DerivativePayoffType.LINEAR.value == "LINEAR"
        assert DerivativePayoffType.NON_LINEAR.value == "NON_LINEAR"
        assert DerivativePayoffType.OTHER.value == "OTHER"

    def test_payoff_type_count(self):
        """All expected payoff types are present."""
        assert len(list(DerivativePayoffType)) == 3


class TestDerivativeValuation:
    """Test DerivativeValuation model."""

    def test_valid_positive_fair_value(self):
        """Valid valuation with positive fair value."""
        valuation = DerivativeValuation(
            fair_value_base_ccy=Decimal("50000"),
            valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
        )
        assert valuation.fair_value_base_ccy == Decimal("50000")

    def test_valid_negative_fair_value(self):
        """Valid valuation with negative fair value."""
        valuation = DerivativeValuation(
            fair_value_base_ccy=Decimal("-25000"),
            valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
        )
        assert valuation.fair_value_base_ccy == Decimal("-25000")

    def test_valid_zero_fair_value(self):
        """Valid valuation with zero fair value."""
        valuation = DerivativeValuation(
            fair_value_base_ccy=Decimal("0"),
            valuation_source=DerivativeValuationSource.FUTURE_PRICER,
        )
        assert valuation.fair_value_base_ccy == Decimal("0")

    def test_rejects_empty_pricing_model(self):
        """Pricing model cannot be empty string."""
        with pytest.raises(ValueError, match="pricing_model must be non-empty"):
            DerivativeValuation(
                fair_value_base_ccy=Decimal("50000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
                pricing_model="",
            )

    def test_valid_with_pricing_model_and_date(self):
        """Valid with pricing model and valuation date."""
        valuation = DerivativeValuation(
            fair_value_base_ccy=Decimal("50000"),
            valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            pricing_model="Black-Scholes",
            valuation_date=date(2026, 6, 10),
        )
        assert valuation.pricing_model == "Black-Scholes"
        assert valuation.valuation_date == date(2026, 6, 10)


class TestDerivativeExposure:
    """Test DerivativeExposure model."""

    def test_valid_notional_only(self):
        """Valid exposure with notional only."""
        exposure = DerivativeExposure(
            notional_base_ccy=Decimal("1000000"),
            exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
        )
        assert exposure.notional_base_ccy == Decimal("1000000")

    def test_valid_equivalent_underlying_only(self):
        """Valid exposure with equivalent underlying only."""
        exposure = DerivativeExposure(
            equivalent_underlying_exposure_base_ccy=Decimal("950000"),
            exposure_source=DerivativeExposureSource.PROVIDED_EQUIVALENT_UNDERLYING,
        )
        assert exposure.equivalent_underlying_exposure_base_ccy == Decimal("950000")

    def test_valid_delta_adjusted_only(self):
        """Valid exposure with delta-adjusted only."""
        exposure = DerivativeExposure(
            delta_adjusted_exposure_base_ccy=Decimal("500000"),
            exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
        )
        assert exposure.delta_adjusted_exposure_base_ccy == Decimal("500000")

    def test_valid_all_exposures_provided(self):
        """Valid with all exposure fields provided."""
        exposure = DerivativeExposure(
            notional_base_ccy=Decimal("1000000"),
            equivalent_underlying_exposure_base_ccy=Decimal("950000"),
            delta_adjusted_exposure_base_ccy=Decimal("500000"),
            exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
        )
        assert exposure.notional_base_ccy == Decimal("1000000")
        assert exposure.equivalent_underlying_exposure_base_ccy == Decimal("950000")
        assert exposure.delta_adjusted_exposure_base_ccy == Decimal("500000")

    def test_rejects_negative_notional(self):
        """Notional cannot be negative."""
        with pytest.raises(ValueError, match="notional_base_ccy must be non-negative"):
            DerivativeExposure(
                notional_base_ccy=Decimal("-100000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            )

    def test_rejects_negative_equivalent_underlying(self):
        """Equivalent underlying cannot be negative."""
        with pytest.raises(
            ValueError, match="equivalent_underlying_exposure_base_ccy must be non-negative"
        ):
            DerivativeExposure(
                equivalent_underlying_exposure_base_ccy=Decimal("-100000"),
                exposure_source=DerivativeExposureSource.PROVIDED_EQUIVALENT_UNDERLYING,
            )

    def test_rejects_negative_delta_adjusted(self):
        """Delta-adjusted cannot be negative."""
        with pytest.raises(
            ValueError, match="delta_adjusted_exposure_base_ccy must be non-negative"
        ):
            DerivativeExposure(
                delta_adjusted_exposure_base_ccy=Decimal("-100000"),
                exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
            )

    def test_allows_unknown_source_without_exposure(self):
        """UNKNOWN source allows no exposure fields."""
        exposure = DerivativeExposure(exposure_source=DerivativeExposureSource.UNKNOWN)
        assert exposure.notional_base_ccy is None


class TestDerivativeRecord:
    """Test DerivativeRecord model."""

    def test_valid_option_record(self):
        """Valid option record."""
        record = DerivativeRecord(
            derivative_id="OPT-001",
            derivative_type=DerivativeType.OPTION,
            payoff_type=DerivativePayoffType.NON_LINEAR,
            underlying_identifier="US0378331005",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("150000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            ),
            exposure=DerivativeExposure(
                delta_adjusted_exposure_base_ccy=Decimal("75000"),
                exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
            ),
        )
        assert record.derivative_id == "OPT-001"
        assert record.payoff_type == DerivativePayoffType.NON_LINEAR

    def test_valid_swap_record(self):
        """Valid swap record."""
        record = DerivativeRecord(
            derivative_id="SWAP-001",
            derivative_type=DerivativeType.SWAP,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier=None,
            currency="EUR",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("-50000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("10000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            ),
        )
        assert record.underlying_identifier is None
        assert record.valuation.fair_value_base_ccy == Decimal("-50000")

    def test_valid_future_record(self):
        """Valid future record."""
        record = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                equivalent_underlying_exposure_base_ccy=Decimal("5000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_EQUIVALENT_UNDERLYING,
            ),
        )
        assert record.derivative_type == DerivativeType.FUTURE

    def test_rejects_empty_derivative_id(self):
        """Derivative ID cannot be empty."""
        with pytest.raises(ValueError, match="derivative_id must be non-empty"):
            DerivativeRecord(
                derivative_id="",
                derivative_type=DerivativeType.OPTION,
                payoff_type=DerivativePayoffType.NON_LINEAR,
                underlying_identifier="US0378331005",
                currency="USD",
                valuation=DerivativeValuation(
                    fair_value_base_ccy=Decimal("150000"),
                    valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
                ),
                exposure=DerivativeExposure(
                    delta_adjusted_exposure_base_ccy=Decimal("75000"),
                    exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
                ),
            )

    def test_rejects_empty_currency(self):
        """Currency cannot be empty."""
        with pytest.raises(ValueError, match="currency must be non-empty"):
            DerivativeRecord(
                derivative_id="OPT-001",
                derivative_type=DerivativeType.OPTION,
                payoff_type=DerivativePayoffType.NON_LINEAR,
                underlying_identifier="US0378331005",
                currency="",
                valuation=DerivativeValuation(
                    fair_value_base_ccy=Decimal("150000"),
                    valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
                ),
                exposure=DerivativeExposure(
                    delta_adjusted_exposure_base_ccy=Decimal("75000"),
                    exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
                ),
            )

    def test_rejects_empty_underlying_identifier(self):
        """Underlying identifier, if provided, cannot be empty."""
        with pytest.raises(ValueError, match="underlying_identifier must be non-empty"):
            DerivativeRecord(
                derivative_id="OPT-001",
                derivative_type=DerivativeType.OPTION,
                payoff_type=DerivativePayoffType.NON_LINEAR,
                underlying_identifier="",
                currency="USD",
                valuation=DerivativeValuation(
                    fair_value_base_ccy=Decimal("150000"),
                    valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
                ),
                exposure=DerivativeExposure(
                    delta_adjusted_exposure_base_ccy=Decimal("75000"),
                    exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
                ),
            )


class TestDerivativeExposureEngine:
    """Test derivative exposure calculation."""

    @pytest.fixture
    def engine(self):
        """Derivative exposure engine."""
        return DerivativeExposureEngine()

    def test_empty_derivative_records(self, engine):
        """Empty derivative records return None source contribution."""
        result = engine.calculate([])

        assert len(result.derivative_records) == 0
        assert result.source_contribution is None
        assert len(result.unsupported_exposures) == 0
        assert len(result.warnings) == 0

    def test_uses_delta_adjusted_exposure_first(self, engine):
        """Engine uses delta-adjusted exposure when all three are provided."""
        record = DerivativeRecord(
            derivative_id="OPT-001",
            derivative_type=DerivativeType.OPTION,
            payoff_type=DerivativePayoffType.NON_LINEAR,
            underlying_identifier="US0378331005",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("150000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                equivalent_underlying_exposure_base_ccy=Decimal("950000"),
                delta_adjusted_exposure_base_ccy=Decimal("500000"),
                exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("500000")

    def test_falls_back_to_equivalent_underlying(self, engine):
        """Engine falls back to equivalent underlying when delta-adjusted not provided."""
        record = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                equivalent_underlying_exposure_base_ccy=Decimal("950000"),
                exposure_source=DerivativeExposureSource.PROVIDED_EQUIVALENT_UNDERLYING,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("950000")

    def test_falls_back_to_notional(self, engine):
        """Engine falls back to notional when other exposures not provided."""
        record = DerivativeRecord(
            derivative_id="FUT-002",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("1000000")

    def test_fair_value_not_used_as_exposure(self, engine):
        """Fair value is not used as leverage exposure."""
        record = DerivativeRecord(
            derivative_id="OPT-001",
            derivative_type=DerivativeType.OPTION,
            payoff_type=DerivativePayoffType.NON_LINEAR,
            underlying_identifier="US0378331005",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("500000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            ),
            exposure=DerivativeExposure(
                delta_adjusted_exposure_base_ccy=Decimal("75000"),
                exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution.gross_exposure == Decimal("75000")
        assert result.source_contribution.gross_exposure != Decimal("500000")

    def test_no_usable_exposure_creates_unsupported(self, engine):
        """Derivative without usable exposure creates unsupported record."""
        record = DerivativeRecord(
            derivative_id="SWAP-001",
            derivative_type=DerivativeType.SWAP,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier=None,
            currency="EUR",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("-50000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(exposure_source=DerivativeExposureSource.FUTURE_CONVERTER),
        )

        result = engine.calculate([record])

        assert result.source_contribution is None
        assert len(result.unsupported_exposures) == 1
        assert len(result.warnings) == 1
        assert "SWAP-001" in result.warnings[0]

    def test_multiple_derivatives_aggregate(self, engine):
        """Multiple derivatives aggregate into single source contribution."""
        record1 = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                equivalent_underlying_exposure_base_ccy=Decimal("5000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_EQUIVALENT_UNDERLYING,
            ),
        )
        record2 = DerivativeRecord(
            derivative_id="OPT-001",
            derivative_type=DerivativeType.OPTION,
            payoff_type=DerivativePayoffType.NON_LINEAR,
            underlying_identifier="AAPL",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("100000"),
                valuation_source=DerivativeValuationSource.PROVIDED_MODEL_VALUE,
            ),
            exposure=DerivativeExposure(
                delta_adjusted_exposure_base_ccy=Decimal("250000"),
                exposure_source=DerivativeExposureSource.PROVIDED_DELTA_ADJUSTED,
            ),
        )

        result = engine.calculate([record1, record2])

        assert result.source_contribution is not None
        assert result.source_contribution.gross_exposure == Decimal("5250000")

    def test_source_contribution_treatment_pending(self, engine):
        """Source contribution treatment is PENDING_METHOD_RULE."""
        record = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution.treatment == ExposureTreatment.PENDING_METHOD_RULE

    def test_source_contribution_commitment_none(self, engine):
        """Source contribution has None commitment_exposure at source layer."""
        record = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution.commitment_exposure is None

    def test_result_model_is_frozen(self, engine):
        """Result model is immutable."""
        result = engine.calculate([])

        with pytest.raises(Exception):  # Pydantic raises on frozen model
            result.source_contributions = []

    def test_derivative_source_is_correct(self, engine):
        """Source is DERIVATIVE."""
        record = DerivativeRecord(
            derivative_id="FUT-001",
            derivative_type=DerivativeType.FUTURE,
            payoff_type=DerivativePayoffType.LINEAR,
            underlying_identifier="ES",
            currency="USD",
            valuation=DerivativeValuation(
                fair_value_base_ccy=Decimal("0"),
                valuation_source=DerivativeValuationSource.PROVIDED_MARKET_VALUE,
            ),
            exposure=DerivativeExposure(
                notional_base_ccy=Decimal("1000000"),
                exposure_source=DerivativeExposureSource.PROVIDED_NOTIONAL,
            ),
        )

        result = engine.calculate([record])

        assert result.source_contribution.source == LeverageSource.DERIVATIVE
