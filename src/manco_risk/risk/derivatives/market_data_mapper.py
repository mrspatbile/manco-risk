"""Mapper from derivative market data to pricing inputs.

Pure conversion layer: transforms DerivativeMarketData contracts into
EuropeanEquityOptionPricingInput contracts for pricing engines.

Selection strategy (this issue):
- Exact maturity matching only (no interpolation)
- Exact ATM (moneyness=1.0) volatility matching
- Clear errors if required points are missing
"""

from datetime import date
from decimal import Decimal

from manco_risk.market_data.derivative_schemas import DerivativeMarketData
from manco_risk.risk.derivatives.pricing_models import (
    EuropeanEquityOptionPricingInput,
    OptionType,
)


class EuropeanOptionMarketDataMapper:
    """Maps derivative market data to European option pricing input.

    Extracts rates, yields, and volatility from market-data curves/surfaces
    and combines with option parameters to create pricing inputs.

    Strategy:
    - Exact maturity matching for risk-free and dividend curves
    - Exact ATM (moneyness=1.0) matching for volatility
    - No interpolation; raises ValueError if exact points missing
    """

    def to_pricing_input(
        self,
        *,
        derivative_id: str,
        option_type: str,
        strike: Decimal,
        maturity_years: Decimal,
        maturity_date: date,
        quantity: Decimal,
        market_data: DerivativeMarketData,
        contract_multiplier: Decimal = Decimal("1"),
    ) -> EuropeanEquityOptionPricingInput:
        """Convert market data and option parameters to pricing input.

        Parameters
        ----------
        derivative_id
            Option identifier (non-empty).
        option_type
            "CALL" or "PUT" (or OptionType enum value).
        strike
            Strike price (must be > 0).
        maturity_years
            Years to maturity (must be > 0).
        maturity_date
            Calendar date of maturity (must be after pricing_date).
        quantity
            Number of contracts (must be non-zero).
        market_data
            DerivativeMarketData with rates, yields, volatility.
        contract_multiplier
            Contract multiplier/notional scale (default 1, must be > 0).

        Returns
        -------
        EuropeanEquityOptionPricingInput
            Pricing input with extracted rates/yields/vol.

        Raises
        ------
        ValueError
            If any required point is missing, validation fails, or parameters invalid.
        """
        # Validate inputs
        self._validate_inputs(
            strike, maturity_years, maturity_date, quantity, contract_multiplier, market_data
        )

        # Convert option type string to enum if needed
        if isinstance(option_type, str):
            option_type_enum = OptionType[option_type.upper()]
        else:
            option_type_enum = option_type

        # Extract risk-free rate at exact maturity
        risk_free_rate = self._extract_risk_free_rate(maturity_years, market_data)

        # Extract dividend yield (default to zero if no dividend curve)
        if market_data.dividend_yield_curve is not None:
            dividend_yield = self._extract_dividend_yield(maturity_years, market_data)
        else:
            dividend_yield = Decimal("0")

        # Extract ATM volatility
        volatility = self._extract_volatility(maturity_years, market_data)

        return EuropeanEquityOptionPricingInput(
            derivative_id=derivative_id,
            pricing_date=market_data.pricing_date,
            option_type=option_type_enum,
            spot=market_data.spot_price,
            strike=strike,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=volatility,
            maturity_date=maturity_date,
            quantity=quantity,
            currency=market_data.currency,
        )

    def _validate_inputs(
        self,
        strike: Decimal,
        maturity_years: Decimal,
        maturity_date: date,
        quantity: Decimal,
        contract_multiplier: Decimal,
        market_data: DerivativeMarketData,
    ) -> None:
        """Validate all input parameters.

        Raises
        ------
        ValueError
            If any parameter is invalid.
        """
        if strike <= Decimal("0"):
            raise ValueError(f"strike must be positive, got {strike}")

        if maturity_years <= Decimal("0"):
            raise ValueError(f"maturity_years must be positive, got {maturity_years}")

        if maturity_date <= market_data.pricing_date:
            raise ValueError(
                f"maturity_date {maturity_date} must be after "
                f"pricing_date {market_data.pricing_date}"
            )

        if quantity == Decimal("0"):
            raise ValueError("quantity must be non-zero")

        if contract_multiplier <= Decimal("0"):
            raise ValueError(f"contract_multiplier must be positive, got {contract_multiplier}")

        if market_data.volatility_surface is None:
            raise ValueError("volatility_surface is required for option pricing")

    def _extract_risk_free_rate(
        self, maturity_years: Decimal, market_data: DerivativeMarketData
    ) -> Decimal:
        """Extract risk-free rate at exact maturity from yield curve.

        Performs exact maturity matching; no interpolation.

        Parameters
        ----------
        maturity_years
            Target maturity in years.
        market_data
            Market data with risk-free curve.

        Returns
        -------
        Decimal
            Risk-free rate as decimal (0.05 = 5%).

        Raises
        ------
        ValueError
            If exact maturity point not found.
        """
        for point in market_data.risk_free_curve.points:
            if point.maturity_years == maturity_years:
                return point.yield_rate

        raise ValueError(
            f"Risk-free curve has no exact point at maturity {maturity_years} years. "
            f"Available maturities: "
            f"{[str(p.maturity_years) for p in market_data.risk_free_curve.points]}"
        )

    def _extract_dividend_yield(
        self, maturity_years: Decimal, market_data: DerivativeMarketData
    ) -> Decimal:
        """Extract dividend yield at exact maturity from dividend curve.

        Performs exact maturity matching; no interpolation.

        Parameters
        ----------
        maturity_years
            Target maturity in years.
        market_data
            Market data with dividend yield curve.

        Returns
        -------
        Decimal
            Dividend yield as decimal (0.02 = 2%).

        Raises
        ------
        ValueError
            If exact maturity point not found.
        """
        if market_data.dividend_yield_curve is None:
            raise ValueError("dividend_yield_curve is None")

        for point in market_data.dividend_yield_curve.points:
            if point.maturity_years == maturity_years:
                return point.yield_rate

        raise ValueError(
            f"Dividend yield curve has no exact point at maturity {maturity_years} years. "
            f"Available maturities: "
            f"{[str(p.maturity_years) for p in market_data.dividend_yield_curve.points]}"
        )

    def _extract_volatility(
        self, maturity_years: Decimal, market_data: DerivativeMarketData
    ) -> Decimal:
        """Extract ATM volatility at exact maturity and moneyness=1.0.

        Performs exact grid-point matching; no interpolation.
        Uses moneyness=1.0 (at-the-money) for this issue.

        Parameters
        ----------
        maturity_years
            Target maturity in years.
        market_data
            Market data with volatility surface.

        Returns
        -------
        Decimal
            Implied volatility as decimal (0.20 = 20%).

        Raises
        ------
        ValueError
            If exact (maturity, moneyness=1.0) point not found.
        """
        if market_data.volatility_surface is None:
            raise ValueError("volatility_surface is None")

        target_moneyness = Decimal("1")

        for point in market_data.volatility_surface.points:
            if point.maturity_years == maturity_years and point.moneyness == target_moneyness:
                return point.implied_volatility

        raise ValueError(
            f"Volatility surface has no exact point at maturity {maturity_years} years "
            f"and moneyness {target_moneyness}. "
            f"Available grid points (maturity, moneyness): "
            f"{[(str(p.maturity_years), str(p.moneyness)) for p in market_data.volatility_surface.points]}"
        )
