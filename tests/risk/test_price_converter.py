"""Tests for PriceToReturnConverter engine."""

from datetime import date
from decimal import Decimal

import pytest

from manco_risk.risk.engines.price_converter import PriceToReturnConverter
from manco_risk.risk.exceptions import InsufficientPriceDataError
from manco_risk.risk.models.price_return import PricePoint, PriceToReturnInput


@pytest.fixture
def converter():
    """Create a PriceToReturnConverter instance."""
    return PriceToReturnConverter()


def test_convert_single_isin_two_prices(converter):
    """Two prices for one ISIN produces one return."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return = 102/100 - 1 = 0.02
    assert result.num_isins == 1
    assert result.num_price_points == 2
    assert result.num_returns == 1
    assert result.num_unique_return_dates == 1
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0.02")


def test_convert_single_isin_three_prices(converter):
    """Three prices produce two returns."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 3), price=Decimal("99")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return 1 = 102/100 - 1 = 0.02
    # Return 2 = 99/102 - 1 ≈ -0.02941176...
    assert result.num_returns == 2
    assert result.num_unique_return_dates == 2
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0.02")
    assert result.historical_returns["US0378331005"][date(2024, 1, 3)] == Decimal("99") / Decimal(
        "102"
    ) - Decimal("1")


def test_convert_single_isin_unsorted_prices(converter):
    """Unsorted prices are sorted before conversion."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 3), price=Decimal("99")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # After sorting: 100 (1/1), 102 (1/2), 99 (1/3)
    # Returns: 102/100 - 1 = 0.02, 99/102 - 1 ≈ -0.02941...
    assert result.num_returns == 2
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0.02")


def test_convert_price_up_10_percent(converter):
    """Price up 10% produces +0.10 return."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("110")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0.10")


def test_convert_price_down_5_percent(converter):
    """Price down 5% produces -0.05 return."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("95")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("-0.05")


def test_convert_price_unchanged_zero_return(converter):
    """Price unchanged produces 0.00 return."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("100")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0")


def test_convert_multiple_isins_independent(converter):
    """Multiple ISINs converted independently."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("110")),
        PricePoint(isin="IE00B4L5Y983", price_date=date(2024, 1, 1), price=Decimal("50")),
        PricePoint(isin="IE00B4L5Y983", price_date=date(2024, 1, 2), price=Decimal("48")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # US0378331005: 110/100 - 1 = 0.10
    # IE00B4L5Y983: 48/50 - 1 = -0.04
    assert result.num_isins == 2
    assert result.num_returns == 2
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("0.10")
    assert result.historical_returns["IE00B4L5Y983"][date(2024, 1, 2)] == Decimal("-0.04")


def test_convert_scenario_date_is_later_price_date(converter):
    """Scenario date is the later date of the price pair."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return date should be 2024-01-02 (the later date)
    assert date(2024, 1, 2) in result.historical_returns["US0378331005"]
    assert date(2024, 1, 1) not in result.historical_returns["US0378331005"]


def test_convert_insufficient_single_price(converter):
    """Single price for an ISIN raises InsufficientPriceDataError."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
    ]
    input = PriceToReturnInput(price_points=points)

    with pytest.raises(InsufficientPriceDataError, match="US0378331005"):
        converter.convert(input)


def test_convert_decimal_precision_preserved(converter):
    """Decimal precision is preserved through calculation."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100.00")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("100.01")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return = 100.01 / 100.00 - 1 = 0.0001
    # Full precision should be preserved (not rounded to 0.0001)
    expected_return = Decimal("100.01") / Decimal("100.00") - Decimal("1")
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == expected_return


def test_convert_counts_correct(converter):
    """Result counts are correct."""
    points = [
        # ISIN 1: 3 prices
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("102")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 3), price=Decimal("99")),
        # ISIN 2: 2 prices
        PricePoint(isin="IE00B4L5Y983", price_date=date(2024, 1, 2), price=Decimal("50")),
        PricePoint(isin="IE00B4L5Y983", price_date=date(2024, 1, 3), price=Decimal("52")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    assert result.num_isins == 2
    assert result.num_price_points == 5
    assert result.num_returns == 3  # 2 for ISIN 1, 1 for ISIN 2
    assert result.num_unique_return_dates == 2  # dates 1/2 and 1/3


def test_convert_negative_return(converter):
    """Negative returns are signed correctly."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("150")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("147")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return = 147/150 - 1 = -0.02
    return_value = result.historical_returns["US0378331005"][date(2024, 1, 2)]
    assert return_value < Decimal("0")
    assert return_value == Decimal("-0.02")


def test_convert_gap_in_dates_not_filled(converter):
    """Gap in price dates is not automatically filled."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        # Gap on 1/2 (e.g., weekend or holiday)
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 3), price=Decimal("102")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return should use consecutive trading observations: 102/100 - 1 = 0.02
    # Scenario date is 2024-01-03 (the later date in the pair)
    assert result.num_returns == 1
    assert result.historical_returns["US0378331005"][date(2024, 1, 3)] == Decimal("0.02")


def test_convert_large_price_movement(converter):
    """Large price movements are handled correctly."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("100")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("200")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return = 200/100 - 1 = 1.00 (100% gain)
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == Decimal("1.00")


def test_convert_small_fractional_return(converter):
    """Small fractional returns are preserved."""
    points = [
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 1), price=Decimal("1000")),
        PricePoint(isin="US0378331005", price_date=date(2024, 1, 2), price=Decimal("1000.10")),
    ]
    input = PriceToReturnInput(price_points=points)
    result = converter.convert(input)

    # Return = 1000.10 / 1000 - 1 = 0.0001
    expected = Decimal("1000.10") / Decimal("1000") - Decimal("1")
    assert result.historical_returns["US0378331005"][date(2024, 1, 2)] == expected
