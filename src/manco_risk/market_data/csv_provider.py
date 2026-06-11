"""CSV-backed market data provider."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from manco_risk.common import (
    FXRateNotAvailableError,
    InsufficientPriceDataError,
    SecurityNotFoundError,
)

from .provider import MarketDataProvider
from .schemas import FXRate, InstrumentInfo, Price, PriceHistory


class CSVProvider(MarketDataProvider):
    """Market data provider backed by CSV files.

    Loads instrument metadata, price history, and FX rates from CSV files
    in the specified data directory.

    CSV files required:
    - instruments.csv: columns = security_id, name, asset_class, currency,
                       maturity_date, coupon_rate, modified_duration_years,
                       spread_duration_years, beta
    - prices.csv: columns = date, security_id, price
    - fx_rates.csv: columns = date, from_currency, to_currency, rate

    Data Quality
    -----------
    The CSV data is the source of truth. Values in CSV files are used as-is
    without transformation or correction. If CSV data contains known anomalies,
    inconsistencies, or provider-specific quirks, they should be documented
    in the CSV metadata and handled at this provider level (not delegated to
    risk engines or ETL).

    For complete guidance on provider-specific transformations, see ARCHITECTURE.md.

    Parameters
    ----------
    data_dir : str or Path
        Directory containing the CSV files
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self._instruments = self._load_instruments()
        self._prices = self._load_prices()
        self._fx_rates = self._load_fx_rates()

    def get_instrument_info(self, security_id: str) -> InstrumentInfo:
        """Retrieve instrument metadata."""
        if security_id not in self._instruments:
            raise SecurityNotFoundError(f"Security not found: {security_id}")
        return self._instruments[security_id]

    def get_price(self, security_id: str, target_date: date) -> Price:
        """Get price on a specific date.

        If exact date not found, returns price on the nearest previous
        business day available in the data.

        Raises
        ------
        SecurityNotFoundError
            If security not found
        InsufficientPriceDataError
            If no price available on or before target date
        """
        if security_id not in self._prices:
            raise SecurityNotFoundError(f"Security not found: {security_id}")

        prices = self._prices[security_id]
        prices_on_or_before = prices[prices["date"] <= target_date]

        if prices_on_or_before.empty:
            raise InsufficientPriceDataError(
                f"No price available for {security_id} on or before {target_date}"
            )

        latest_row = prices_on_or_before.iloc[-1]
        return Price(
            security_id=security_id,
            date=latest_row["date"],
            price=latest_row["price"],
            currency=latest_row["currency"],
        )

    def get_price_history(
        self,
        security_id: str,
        start_date: date,
        end_date: date,
    ) -> PriceHistory:
        """Get price history over a date range.

        Returns only prices available in the data; no gaps are filled.
        Missing business days are explicit (not forward-filled).

        Raises
        ------
        SecurityNotFoundError
            If security not found
        InsufficientPriceDataError
            If no prices within the range
        """
        if security_id not in self._prices:
            raise SecurityNotFoundError(f"Security not found: {security_id}")

        prices_df = self._prices[security_id]
        prices_in_range = prices_df[
            (prices_df["date"] >= start_date) & (prices_df["date"] <= end_date)
        ]

        if prices_in_range.empty:
            raise InsufficientPriceDataError(
                f"No prices for {security_id} between {start_date} and {end_date}"
            )

        price_objects = [
            Price(
                security_id=security_id,
                date=row["date"],
                price=row["price"],
                currency=row["currency"],
            )
            for _, row in prices_in_range.iterrows()
        ]

        return PriceHistory(security_id=security_id, prices=price_objects)

    def get_fx_rate(
        self,
        from_currency: str,
        to_currency: str,
        target_date: date,
    ) -> FXRate:
        """Get FX rate on a specific date.

        If exact date not found, returns rate on the nearest previous
        business day available in the data.

        Raises
        ------
        FXRateNotAvailableError
            If rate not available for the currency pair and date
        """
        key = (from_currency, to_currency)

        if key not in self._fx_rates:
            raise FXRateNotAvailableError(f"No rate available for {from_currency}/{to_currency}")

        rates_df = self._fx_rates[key]
        rates_on_or_before = rates_df[rates_df["date"] <= target_date]

        if rates_on_or_before.empty:
            raise FXRateNotAvailableError(
                f"No rate available for {from_currency}/{to_currency} on or before {target_date}"
            )

        latest_row = rates_on_or_before.iloc[-1]
        return FXRate(
            from_currency=from_currency,
            to_currency=to_currency,
            date=latest_row["date"],
            rate=latest_row["rate"],
        )

    def _load_instruments(self) -> dict[str, InstrumentInfo]:
        """Load instrument reference data from CSV."""
        csv_path = self.data_dir / "instruments.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Instruments file not found: {csv_path}")

        df = pd.read_csv(csv_path, dtype={"security_id": str})

        instruments = {}
        for _, row in df.iterrows():
            info = InstrumentInfo(
                security_id=row["security_id"],
                name=row["name"],
                asset_class=row["asset_class"],
                currency=row["currency"],
                maturity_date=pd.to_datetime(row["maturity_date"]).date()
                if pd.notna(row["maturity_date"])
                else None,
                coupon_rate=Decimal(str(row["coupon_rate"]))
                if pd.notna(row["coupon_rate"])
                else None,
                modified_duration_years=Decimal(str(row["modified_duration_years"]))
                if pd.notna(row["modified_duration_years"])
                else None,
                spread_duration_years=Decimal(str(row["spread_duration_years"]))
                if pd.notna(row["spread_duration_years"])
                else None,
                beta=Decimal(str(row["beta"])) if pd.notna(row["beta"]) else None,
            )
            instruments[info.security_id] = info

        return instruments

    def _load_prices(self) -> dict[str, pd.DataFrame]:
        """Load price history from CSV and index by security."""
        csv_path = self.data_dir / "prices.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Prices file not found: {csv_path}")

        df = pd.read_csv(
            csv_path,
            dtype={"security_id": str, "price": str},
        )

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["price"] = df["price"].apply(lambda x: Decimal(str(x)))  # type: ignore[arg-type, return-value]

        df = df.sort_values("date").reset_index(drop=True)

        prices_by_security: dict[str, pd.DataFrame] = {}
        for security_id, group in df.groupby("security_id"):
            prices_by_security[str(security_id)] = group.reset_index(drop=True)

        return prices_by_security

    def _load_fx_rates(self) -> dict[tuple[str, str], pd.DataFrame]:
        """Load FX rates from CSV and index by (from_currency, to_currency)."""
        csv_path = self.data_dir / "fx_rates.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"FX rates file not found: {csv_path}")

        df = pd.read_csv(
            csv_path,
            dtype={
                "from_currency": str,
                "to_currency": str,
                "rate": str,
            },
        )

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["rate"] = df["rate"].apply(lambda x: Decimal(str(x)))  # type: ignore[arg-type, return-value]

        df = df.sort_values("date").reset_index(drop=True)

        rates_by_pair: dict[tuple[str, str], pd.DataFrame] = {}
        for (from_ccy, to_ccy), group in df.groupby(["from_currency", "to_currency"]):
            rates_by_pair[(str(from_ccy), str(to_ccy))] = group.reset_index(drop=True)

        return rates_by_pair
