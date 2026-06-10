"""Price-to-return converter for equity-like instruments.

Converts historical price series into the return format expected by
EquityScenarioPnLGenerator: dict[str, dict[date, Decimal]].
"""

from datetime import date
from decimal import Decimal

from manco_risk.risk.exceptions import InsufficientPriceDataError
from manco_risk.risk.models.price_return import (
    PriceToReturnInput,
    PriceToReturnResult,
)


class PriceToReturnConverter:
    """Convert historical price series to returns format.

    For each ISIN:
    1. Collect price observations
    2. Sort by price_date
    3. Compute 1-day returns: return_t = price_t / price_(t-1) - 1
    4. Use later date as scenario date

    The converter does not forward-fill, drop observations, or use proxies.
    All price data must be present and valid.
    """

    def convert(self, input: PriceToReturnInput) -> PriceToReturnResult:
        """Convert prices to returns.

        Parameters
        ----------
        input : PriceToReturnInput
            Price observations for one or more ISINs.

        Returns
        -------
        PriceToReturnResult
            Historical returns dict ready for equity scenario generator.

        Raises
        ------
        InvalidPriceDataError
            If price data validation fails.
        InsufficientPriceDataError
            If an ISIN has fewer than 2 price observations.
        """
        # Group price points by ISIN
        prices_by_isin: dict[str, list] = {}
        for point in input.price_points:
            if point.isin not in prices_by_isin:
                prices_by_isin[point.isin] = []
            prices_by_isin[point.isin].append(point)

        # Convert to returns for each ISIN
        historical_returns: dict[str, dict[date, Decimal]] = {}
        total_returns = 0
        unique_return_dates: set[date] = set()

        for isin, price_points in prices_by_isin.items():
            # Validate at least 2 observations
            if len(price_points) < 2:
                raise InsufficientPriceDataError(isin, len(price_points))

            # Sort by price_date
            sorted_points = sorted(price_points, key=lambda p: p.price_date)

            # Compute 1-day returns from consecutive pairs
            returns_dict: dict[date, Decimal] = {}
            for i in range(1, len(sorted_points)):
                price_prev = sorted_points[i - 1].price
                price_curr = sorted_points[i].price
                scenario_date = sorted_points[i].price_date

                # Compute return: (price_t / price_t-1) - 1
                # Do not round or quantize; preserve full Decimal precision
                return_value = price_curr / price_prev - Decimal("1")

                returns_dict[scenario_date] = return_value
                unique_return_dates.add(scenario_date)
                total_returns += 1

            historical_returns[isin] = returns_dict

        # Construct result
        result = PriceToReturnResult(
            historical_returns=historical_returns,
            num_isins=len(prices_by_isin),
            num_price_points=len(input.price_points),
            num_returns=total_returns,
            num_unique_return_dates=len(unique_return_dates),
        )

        return result
