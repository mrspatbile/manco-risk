"""Tests for ETL position input schema and CSV loading."""

import csv
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from manco_risk.etl import PositionInput, PositionLoader
from manco_risk.etl.exceptions import PositionCSVLoadError


class TestPositionInputSchema:
    """Tests for PositionInput validation schema."""

    def test_valid_position_required_fields_only(self) -> None:
        """PositionInput accepts valid required fields."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        assert position.fund_name == "Test Fund"
        assert position.valuation_date == date(2025, 1, 15)
        assert position.isin == "IE00B4L5Y983"
        assert position.quantity == Decimal("100")
        assert position.market_value == Decimal("12500")
        assert position.currency == "EUR"
        assert position.source_position_identifier is None
        assert position.market_value_base_ccy_source is None

    def test_valid_position_with_optional_fields(self) -> None:
        """PositionInput accepts optional fields when provided."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
            source_position_identifier="POS-001",
            market_value_base_ccy_source=Decimal("13500"),
        )

        assert position.source_position_identifier == "POS-001"
        assert position.market_value_base_ccy_source == Decimal("13500")

    def test_position_rejects_blank_fund_name(self) -> None:
        """PositionInput rejects blank fund_name."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            )

    def test_position_rejects_whitespace_only_fund_name(self) -> None:
        """PositionInput rejects whitespace-only fund_name."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="   ",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            )

    def test_position_rejects_blank_isin(self) -> None:
        """PositionInput rejects blank isin."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            )

    def test_position_rejects_blank_currency(self) -> None:
        """PositionInput rejects blank currency."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="",
            )

    def test_position_normalizes_currency_to_uppercase(self) -> None:
        """PositionInput normalizes currency to uppercase."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="eur",
        )

        assert position.currency == "EUR"

    def test_position_parses_date_string(self) -> None:
        """PositionInput parses ISO date string."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date="2025-01-15",
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        assert position.valuation_date == date(2025, 1, 15)

    def test_position_rejects_invalid_date_string(self) -> None:
        """PositionInput rejects invalid date string."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="Test Fund",
                valuation_date="2025-13-01",  # Invalid month
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value=Decimal("12500"),
                currency="EUR",
            )

    def test_position_parses_quantity_from_string(self) -> None:
        """PositionInput parses quantity from string."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity="100.5",
            market_value=Decimal("12500"),
            currency="EUR",
        )

        assert position.quantity == Decimal("100.5")

    def test_position_parses_negative_quantity(self) -> None:
        """PositionInput accepts negative quantity (short position)."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("-50"),
            market_value=Decimal("-6250"),
            currency="EUR",
        )

        assert position.quantity == Decimal("-50")

    def test_position_rejects_invalid_quantity(self) -> None:
        """PositionInput rejects invalid quantity."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity="invalid",
                market_value=Decimal("12500"),
                currency="EUR",
            )

    def test_position_rejects_invalid_market_value(self) -> None:
        """PositionInput rejects invalid market_value."""
        with pytest.raises(ValidationError):
            PositionInput(
                fund_name="Test Fund",
                valuation_date=date(2025, 1, 15),
                isin="IE00B4L5Y983",
                quantity=Decimal("100"),
                market_value="not_a_number",
                currency="EUR",
            )

    def test_position_parses_optional_base_ccy_from_string(self) -> None:
        """PositionInput parses market_value_base_ccy_source from string."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
            market_value_base_ccy_source="13500.50",
        )

        assert position.market_value_base_ccy_source == Decimal("13500.50")

    def test_position_treats_empty_string_base_ccy_as_none(self) -> None:
        """PositionInput treats empty string market_value_base_ccy_source as None."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
            market_value_base_ccy_source="",
        )

        assert position.market_value_base_ccy_source is None

    def test_position_is_immutable(self) -> None:
        """PositionInput is immutable (frozen)."""
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("12500"),
            currency="EUR",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            position.fund_name = "Modified"

    def test_position_accepts_zero_quantity(self) -> None:
        """PositionInput accepts zero quantity at ingestion boundary.

        Note: Zero quantity represents a position that was fully closed or unwound.
        Full data quality validation (e.g., rejecting zero positions) is deferred to
        the validation framework (MRS-132). This step validates only parsing and
        required fields, not business logic.
        """
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("0"),
            market_value=Decimal("0"),
            currency="EUR",
        )

        assert position.quantity == Decimal("0")
        assert position.market_value == Decimal("0")

    def test_position_accepts_zero_market_value(self) -> None:
        """PositionInput accepts zero market_value at ingestion boundary.

        Note: Zero market value may represent worthless positions or data entry
        anomalies. Full data quality validation is deferred to the validation
        framework (MRS-132). This step validates only parsing and required fields.
        """
        position = PositionInput(
            fund_name="Test Fund",
            valuation_date=date(2025, 1, 15),
            isin="IE00B4L5Y983",
            quantity=Decimal("100"),
            market_value=Decimal("0"),
            currency="EUR",
        )

        assert position.market_value == Decimal("0")


class TestPositionLoaderCSV:
    """Tests for PositionLoader CSV reading."""

    @pytest.fixture
    def valid_csv_file(self) -> Path:
        """Create a temporary valid CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "market_value": "12500.50",
                    "currency": "EUR",
                }
            )
            writer.writerow(
                {
                    "fund_name": "Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "US0378331005",
                    "quantity": "50",
                    "market_value": "8000.75",
                    "currency": "USD",
                }
            )
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    @pytest.fixture
    def csv_with_optional_fields(self) -> Path:
        """Create a CSV with optional fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                    "source_position_identifier",
                    "market_value_base_ccy_source",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "market_value": "12500",
                    "currency": "EUR",
                    "source_position_identifier": "POS-001",
                    "market_value_base_ccy_source": "13500",
                }
            )
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    def test_load_csv_valid_file(self, valid_csv_file: Path) -> None:
        """PositionLoader loads valid CSV file."""
        positions = PositionLoader.load_csv(valid_csv_file)

        assert len(positions) == 2
        assert positions[0].fund_name == "Test Fund"
        assert positions[0].isin == "IE00B4L5Y983"
        assert positions[0].quantity == Decimal("100")
        assert positions[1].isin == "US0378331005"

    def test_load_csv_with_optional_fields(self, csv_with_optional_fields: Path) -> None:
        """PositionLoader handles CSV with optional fields."""
        positions = PositionLoader.load_csv(csv_with_optional_fields)

        assert len(positions) == 1
        assert positions[0].source_position_identifier == "POS-001"
        assert positions[0].market_value_base_ccy_source == Decimal("13500")

    def test_load_csv_file_not_found(self) -> None:
        """PositionLoader raises error when file not found."""
        with pytest.raises(PositionCSVLoadError, match="File not found"):
            PositionLoader.load_csv("/nonexistent/file.csv")

    def test_load_csv_missing_required_column(self) -> None:
        """PositionLoader raises error when required column is missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    # Missing market_value
                    "currency",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "Test Fund",
                    "valuation_date": "2025-01-15",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "currency": "EUR",
                }
            )
            temp_path = Path(f.name)

        try:
            with pytest.raises(PositionCSVLoadError, match="missing required headers"):
                PositionLoader.load_csv(temp_path)
        finally:
            temp_path.unlink()

    def test_load_csv_invalid_data_in_row(self) -> None:
        """PositionLoader raises error for invalid data in row."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "",  # Invalid: blank fund_name
                    "valuation_date": "2025-01-15",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "market_value": "12500",
                    "currency": "EUR",
                }
            )
            temp_path = Path(f.name)

        try:
            with pytest.raises(PositionCSVLoadError, match="Row 2"):
                PositionLoader.load_csv(temp_path)
        finally:
            temp_path.unlink()

    def test_load_csv_invalid_date_in_row(self) -> None:
        """PositionLoader raises error for invalid date in row."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "fund_name": "Test Fund",
                    "valuation_date": "invalid-date",
                    "isin": "IE00B4L5Y983",
                    "quantity": "100",
                    "market_value": "12500",
                    "currency": "EUR",
                }
            )
            temp_path = Path(f.name)

        try:
            with pytest.raises(PositionCSVLoadError, match="Row 2"):
                PositionLoader.load_csv(temp_path)
        finally:
            temp_path.unlink()

    def test_load_csv_empty_file_with_headers_only(self) -> None:
        """PositionLoader handles empty CSV (headers only)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                ],
            )
            writer.writeheader()
            temp_path = Path(f.name)

        try:
            positions = PositionLoader.load_csv(temp_path)
            assert len(positions) == 0
        finally:
            temp_path.unlink()
