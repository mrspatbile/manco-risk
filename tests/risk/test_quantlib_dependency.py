"""Smoke test for QuantLib dependency.

Verifies that QuantLib can be imported and basic objects can be constructed.
This is NOT a pricing test; only confirms that the dependency is available.

QuantLib is an optional dependency for future derivative pricing work (MRS-169B+).
"""


class TestQuantLibDependency:
    """Test that QuantLib is available and importable."""

    def test_quantlib_imports(self):
        """QuantLib module can be imported."""
        import QuantLib as ql

        assert ql is not None

    def test_quantlib_has_version(self):
        """QuantLib has version information."""
        import QuantLib as ql

        assert hasattr(ql, "__version__")
        version = ql.__version__
        assert isinstance(version, str)
        assert len(version) > 0

    def test_quantlib_simple_date(self):
        """QuantLib can construct a simple date object."""
        import QuantLib as ql

        date = ql.Date(11, 6, 2026)  # June 11, 2026
        assert date is not None
        assert date.dayOfMonth() == 11
        assert date.month() == 6
        assert date.year() == 2026

    def test_quantlib_simple_quote(self):
        """QuantLib can construct a simple quote object."""
        import QuantLib as ql

        quote = ql.SimpleQuote(100.0)
        assert quote is not None
        assert quote.value() == 100.0

    def test_quantlib_calendar(self):
        """QuantLib can construct a calendar object."""
        import QuantLib as ql

        calendar = ql.TARGET()
        assert calendar is not None

    def test_quantlib_daycount(self):
        """QuantLib can construct a day count convention."""
        import QuantLib as ql

        daycount = ql.Actual365Fixed()
        assert daycount is not None

    def test_quantlib_enums_available(self):
        """QuantLib has expected enum types available."""
        import QuantLib as ql

        # Test that key enum types are available
        assert hasattr(ql, "Option")
        assert hasattr(ql, "Period")
        assert hasattr(ql.Option, "Call")
        assert hasattr(ql.Option, "Put")

    def test_no_quantlib_in_production_code(self):
        """QuantLib is not imported in production risk code (yet)."""
        # This test verifies that the core risk modules don't depend on QuantLib
        # Future MRS-169C will wire QuantLib-backed pricing, but for now
        # the risk layer is independent of QuantLib
        import inspect

        import manco_risk.risk.derivatives.manual_pricer as pricer_module

        source = inspect.getsource(pricer_module)
        # Manual pricer should not import QuantLib
        assert "QuantLib" not in source
        assert "import ql" not in source
