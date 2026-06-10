"""Position input schema and CSV loading for manco-risk.

Responsibilities:
- Define validated PositionInput schema
- Load and normalize position data from CSV
- Validate required fields and data types
- Enforce data conventions (dates, decimals, etc.)

Notes:
- Input validation occurs at ingestion boundary.
- No database persistence or ORM records created here.
- No enrichment or derived field calculation.
- Schema defines source data fields only.
"""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from manco_risk.etl.exceptions import PositionCSVLoadError


class PositionInput(BaseModel):
    """Validated position input record from fund administrator file.

    Fields:
    - fund_name: Fund identifier from admin file
    - valuation_date: Valuation date (ISO 8601)
    - isin: Instrument ISIN
    - quantity: Number of shares/units (can be negative for short positions)
    - market_value: Position market value in instrument currency
    - currency: Instrument currency code
    - source_position_identifier: Optional position ID from source system
    - market_value_base_ccy_source: Optional position market value in base currency from admin file
    """

    fund_name: str
    valuation_date: date
    isin: str
    quantity: Decimal
    market_value: Decimal
    currency: str
    source_position_identifier: Optional[str] = None
    market_value_base_ccy_source: Optional[Decimal] = None

    model_config = ConfigDict(frozen=True)

    @field_validator("fund_name")
    @classmethod
    def validate_fund_name(cls, v: str) -> str:
        """Fund name must not be blank."""
        if not v or not v.strip():
            raise ValueError("fund_name must not be blank")
        return v.strip()

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """ISIN must not be blank."""
        if not v or not v.strip():
            raise ValueError("isin must not be blank")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Currency code must not be blank."""
        if not v or not v.strip():
            raise ValueError("currency must not be blank")
        return v.strip().upper()

    @field_validator("valuation_date", mode="before")
    @classmethod
    def parse_valuation_date(cls, v) -> date:
        """Parse valuation_date as ISO date."""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError as e:
                raise ValueError(f"valuation_date must be ISO 8601 date: {e}") from e
        raise ValueError(f"valuation_date must be a date or ISO date string, got {type(v)}")

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v) -> Decimal:
        """Parse quantity as Decimal."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"quantity must be a valid Decimal: {e}") from e

    @field_validator("market_value", mode="before")
    @classmethod
    def parse_market_value(cls, v) -> Decimal:
        """Parse market_value as Decimal."""
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"market_value must be a valid Decimal: {e}") from e

    @field_validator("market_value_base_ccy_source", mode="before")
    @classmethod
    def parse_market_value_base_ccy_source(cls, v) -> Optional[Decimal]:
        """Parse market_value_base_ccy_source as Decimal if present."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        if isinstance(v, Decimal):
            return v
        try:
            return Decimal(str(v))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"market_value_base_ccy_source must be a valid Decimal: {e}") from e


class PositionLoader:
    """Load and validate positions from CSV files."""

    @staticmethod
    def load_csv(csv_file: Path | str) -> list[PositionInput]:
        """Load positions from CSV file.

        Parameters
        ----------
        csv_file : Path | str
            Path to CSV file. File must contain headers.

        Returns
        -------
        list[PositionInput]
            Validated position input records.

        Raises
        ------
        PositionCSVLoadError
            If file cannot be read or contains invalid data.
        """
        csv_path = Path(csv_file)

        if not csv_path.exists():
            raise PositionCSVLoadError(f"File not found: {csv_path}")

        if not csv_path.is_file():
            raise PositionCSVLoadError(f"Path is not a file: {csv_path}")

        positions: list[PositionInput] = []

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if reader.fieldnames is None:
                    raise PositionCSVLoadError("CSV file has no headers")

                required_fields = {
                    "fund_name",
                    "valuation_date",
                    "isin",
                    "quantity",
                    "market_value",
                    "currency",
                }
                missing_fields = required_fields - set(reader.fieldnames)

                if missing_fields:
                    raise PositionCSVLoadError(
                        f"CSV file missing required headers: {', '.join(sorted(missing_fields))}"
                    )

                for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                    try:
                        # Cast row dict to remove type ambiguity for Pydantic
                        row_data: dict[str, str | None] = {k: v for k, v in row.items()}
                        position = PositionInput(**row_data)  # type: ignore[arg-type]
                        positions.append(position)
                    except ValidationError as e:
                        raise PositionCSVLoadError(
                            f"Row {row_num}: Invalid position data - {e}"
                        ) from e

        except PositionCSVLoadError:
            raise
        except Exception as e:
            raise PositionCSVLoadError(f"Error reading CSV file: {e}") from e

        return positions
