"""Tests for common types and enumerations.

Validates that common enums (AssetClass, Currency) have expected values
and maintain contract with database/ETL layers.
"""

from manco_risk.common.types import AssetClass, Currency


class TestAssetClass:
    """Test AssetClass enum."""

    def test_equity_value(self):
        """EQUITY has title-case value for database convention."""
        assert AssetClass.EQUITY.value == "Equity"

    def test_bond_value(self):
        """BOND has title-case value for database convention."""
        assert AssetClass.BOND.value == "Bond"

    def test_fx_value(self):
        """FX has code-like value."""
        assert AssetClass.FX.value == "FX"

    def test_index_value(self):
        """INDEX has title-case value for database convention."""
        assert AssetClass.INDEX.value == "Index"

    def test_cash_value(self):
        """CASH has title-case value for database convention."""
        assert AssetClass.CASH.value == "Cash"

    def test_etf_value(self):
        """ETF has code-like value."""
        assert AssetClass.ETF.value == "ETF"

    def test_listed_fund_value(self):
        """LISTED_FUND has human-readable value."""
        assert AssetClass.LISTED_FUND.value == "Listed Fund"

    def test_all_asset_classes_present(self):
        """All expected asset classes are defined."""
        expected = {"EQUITY", "BOND", "FX", "INDEX", "CASH", "ETF", "LISTED_FUND"}
        actual = {ac.name for ac in AssetClass}
        assert actual == expected

    def test_asset_class_is_str_enum(self):
        """AssetClass members are strings (str enum)."""
        assert isinstance(AssetClass.EQUITY, str)
        assert isinstance(AssetClass.BOND, str)
        assert isinstance(AssetClass.EQUITY.value, str)

    def test_csv_values_matchable(self):
        """CSV asset-class values are matchable against enum values.

        This test documents the ETL contract: CSV loads asset_class as a string,
        and that string should match an AssetClass enum value.
        """
        csv_values = ["Equity", "Bond", "FX", "Index", "Cash", "ETF", "Listed Fund"]
        enum_values = [ac.value for ac in AssetClass]
        for csv_val in csv_values:
            assert csv_val in enum_values, f"CSV value '{csv_val}' not in enum"


class TestCurrency:
    """Test Currency enum."""

    def test_usd_value(self):
        """USD has standard 3-letter code."""
        assert Currency.USD.value == "USD"

    def test_eur_value(self):
        """EUR has standard 3-letter code."""
        assert Currency.EUR.value == "EUR"

    def test_gbp_value(self):
        """GBP has standard 3-letter code."""
        assert Currency.GBP.value == "GBP"

    def test_jpy_value(self):
        """JPY has standard 3-letter code."""
        assert Currency.JPY.value == "JPY"

    def test_all_currencies_present(self):
        """All expected currencies are defined."""
        expected = {"USD", "EUR", "GBP", "JPY"}
        actual = {c.name for c in Currency}
        assert actual == expected

    def test_currency_is_str_enum(self):
        """Currency members are strings (str enum)."""
        assert isinstance(Currency.USD, str)
        assert isinstance(Currency.USD.value, str)
