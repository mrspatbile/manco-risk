"""Tests for price and price-to-return models."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.models.price_return import PricePoint, PriceToReturnInput, PriceToReturnResult


def test_price_point_valid():
    """Valid PricePoint constructs successfully."""
    point = PricePoint(
        isin="US0378331005",
        price_date=date(2024, 1, 1),
        price=Decimal("150.50"),
    )
    assert point.isin == "US0378331005"
    assert point.price_date == date(2024, 1, 1)
    assert point.price == Decimal("150.50")


def test_price_point_empty_isin():
    """Empty ISIN rejected."""
    with pytest.raises(ValueError, match="ISIN must be non-empty"):
        PricePoint(
            isin="",
            price_date=date(2024, 1, 1),
            price=Decimal("150.00"),
        )


def test_price_point_whitespace_isin():
    """Whitespace-only ISIN rejected."""
    with pytest.raises(ValueError, match="ISIN must be non-empty"):
        PricePoint(
            isin="   ",
            price_date=date(2024, 1, 1),
            price=Decimal("150.00"),
        )


def test_price_point_zero_price():
    """Zero price rejected."""
    with pytest.raises(ValueError, match="Price must be strictly positive"):
        PricePoint(
            isin="US0378331005",
            price_date=date(2024, 1, 1),
            price=Decimal("0.00"),
        )


def test_price_point_negative_price():
    """Negative price rejected."""
    with pytest.raises(ValueError, match="Price must be strictly positive"):
        PricePoint(
            isin="US0378331005",
            price_date=date(2024, 1, 1),
            price=Decimal("-100.00"),
        )


def test_price_point_price_from_float():
    """Price as float is converted to Decimal."""
    point = PricePoint(
        isin="US0378331005",
        price_date=date(2024, 1, 1),
        price=150.50,
    )
    assert isinstance(point.price, Decimal)
    assert point.price == Decimal("150.5")


def test_price_point_price_from_int():
    """Price as int is converted to Decimal."""
    point = PricePoint(
        isin="US0378331005",
        price_date=date(2024, 1, 1),
        price=150,
    )
    assert isinstance(point.price, Decimal)
    assert point.price == Decimal("150")


def test_price_point_frozen():
    """PricePoint is frozen."""
    point = PricePoint(
        isin="US0378331005",
        price_date=date(2024, 1, 1),
        price=Decimal("150.00"),
    )
    with pytest.raises(ValueError):
        point.price = Decimal("200.00")


def test_price_to_return_input_valid():
    """Valid PriceToReturnInput constructs."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    assert len(input.price_points) == 2


def test_price_to_return_input_empty():
    """Empty price_points rejected."""
    with pytest.raises(ValueError, match="Price points list must not be empty"):
        PriceToReturnInput(price_points=[])


def test_price_to_return_input_duplicate_isin_date():
    """Duplicate (isin, date) pair rejected."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("102")),
    ]
    with pytest.raises(ValueError, match="Duplicate price point"):
        PriceToReturnInput(price_points=points)


def test_price_to_return_input_frozen():
    """PriceToReturnInput is frozen."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    with pytest.raises(ValueError):
        input.price_points = []


def test_price_to_return_result_valid():
    """Valid PriceToReturnResult constructs."""
    returns = {
        "US0378331005": {
            date(2024, 1, 2): Decimal("0.02"),
        }
    }
    result = PriceToReturnResult(
        historical_returns=returns,
        num_isins=1,
        num_price_points=2,
        num_returns=1,
        num_unique_return_dates=1,
    )
    assert result.num_isins == 1
    assert result.num_returns == 1


def test_price_to_return_result_negative_num_isins():
    """Negative num_isins rejected."""
    with pytest.raises(ValueError, match="Number of ISINs must be non-negative"):
        PriceToReturnResult(
            historical_returns={},
            num_isins=-1,
            num_price_points=0,
            num_returns=0,
            num_unique_return_dates=0,
        )


def test_price_to_return_result_negative_num_price_points():
    """Negative num_price_points rejected."""
    with pytest.raises(ValueError, match="Number of price points must be non-negative"):
        PriceToReturnResult(
            historical_returns={},
            num_isins=0,
            num_price_points=-1,
            num_returns=0,
            num_unique_return_dates=0,
        )


def test_price_to_return_result_negative_num_returns():
    """Negative num_returns rejected."""
    with pytest.raises(ValueError, match="Number of returns must be non-negative"):
        PriceToReturnResult(
            historical_returns={},
            num_isins=0,
            num_price_points=0,
            num_returns=-1,
            num_unique_return_dates=0,
        )


def test_price_to_return_result_negative_num_unique_return_dates():
    """Negative num_unique_return_dates rejected."""
    with pytest.raises(ValueError, match="Number of unique return dates must be non-negative"):
        PriceToReturnResult(
            historical_returns={},
            num_isins=0,
            num_price_points=0,
            num_returns=0,
            num_unique_return_dates=-1,
        )


def test_price_to_return_result_frozen():
    """PriceToReturnResult is frozen."""
    result = PriceToReturnResult(
        historical_returns={},
        num_isins=0,
        num_price_points=0,
        num_returns=0,
        num_unique_return_dates=0,
    )
    with pytest.raises(ValueError):
        result.num_isins = 5
