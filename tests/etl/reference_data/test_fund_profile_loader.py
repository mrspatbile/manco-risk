"""Tests for FundProfileLoader."""

import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from manco_risk.etl.reference_data.fund_profile_loader import FundProfileLoader
from manco_risk.etl.reference_data.models import FundProfile


@pytest.fixture
def temp_funds_dir():
    """Create a temporary funds directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_ucits_balanced(temp_funds_dir):
    """Test loading valid UCITS_Balanced fund profile."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
        "target_nav_eur": 500000000,
        "strategy": "Balanced portfolio",
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    profile = loader.load("UCITS_Balanced")

    assert isinstance(profile, FundProfile)
    assert profile.fund_id == "UCITS_Balanced"
    assert profile.fund_name == "UCITS Balanced"
    assert profile.fund_type == "UCITS"
    assert profile.currency == "EUR"
    assert profile.domicile == "Luxembourg"
    assert profile.inception_date == date(2015, 9, 1)
    assert profile.target_nav_eur == Decimal("500000000")
    assert profile.strategy == "Balanced portfolio"


def test_load_aifm_hedgefund(temp_funds_dir):
    """Test loading valid AIFM_HedgeFund fund profile."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "fund_name": "AIFM Hedge Fund",
        "fund_short_name": "HF",
        "fund_type": "AIFM",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2018-01-15",
        "target_nav_eur": 250000000,
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    profile = loader.load("AIFM_HedgeFund")

    assert profile.fund_id == "AIFM_HedgeFund"
    assert profile.fund_short_name == "HF"
    assert profile.inception_date == date(2018, 1, 15)


def test_load_missing_file(temp_funds_dir):
    """Test error when profile file not found."""
    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="Fund profile not found"):
        loader.load("NonExistent")


def test_load_invalid_json(temp_funds_dir):
    """Test error when JSON is invalid."""
    fund_dir = temp_funds_dir / "BadJSON"
    fund_dir.mkdir()

    with open(fund_dir / "fund_profile.json", "w") as f:
        f.write("{invalid json}")

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="Invalid JSON"):
        loader.load("BadJSON")


def test_fund_id_mismatch(temp_funds_dir):
    """Test error when fund_id in JSON doesn't match folder name."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "WrongFundId",  # Doesn't match folder name
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="fund_id mismatch"):
        loader.load("UCITS_Balanced")


def test_missing_schema_version(temp_funds_dir):
    """Test error when schema_version is missing."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="schema_version is required"):
        loader.load("UCITS_Balanced")


def test_missing_fund_name(temp_funds_dir):
    """Test error when fund_name is missing."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="fund_name is required"):
        loader.load("UCITS_Balanced")


def test_invalid_currency_code(temp_funds_dir):
    """Test error when currency is not 3-letter code."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "INVALID",  # Not 3 letters
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="currency must be 3-letter ISO code"):
        loader.load("UCITS_Balanced")


def test_invalid_inception_date(temp_funds_dir):
    """Test error when inception_date is not ISO 8601."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015/09/01",  # Not ISO 8601
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="inception_date must be ISO 8601 date"):
        loader.load("UCITS_Balanced")


def test_future_inception_date(temp_funds_dir):
    """Test error when inception_date is in the future."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2099-01-01",  # Future date
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="inception_date cannot be in future"):
        loader.load("UCITS_Balanced")


def test_negative_target_nav(temp_funds_dir):
    """Test error when target_nav_eur is negative."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    profile_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "fund_name": "UCITS Balanced",
        "fund_type": "UCITS",
        "currency": "EUR",
        "domicile": "Luxembourg",
        "inception_date": "2015-09-01",
        "target_nav_eur": -1000,  # Negative
    }

    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="target_nav_eur must be a positive number"):
        loader.load("UCITS_Balanced")


def test_load_all(temp_funds_dir):
    """Test loading all fund profiles from directory."""
    # Create two funds
    for fund_id, target_nav in [
        ("UCITS_Balanced", 500000000),
        ("AIFM_HedgeFund", 250000000),
    ]:
        fund_dir = temp_funds_dir / fund_id
        fund_dir.mkdir()

        profile_data = {
            "schema_version": "1.0",
            "fund_id": fund_id,
            "fund_name": f"Fund {fund_id}",
            "fund_type": "UCITS" if "UCITS" in fund_id else "AIFM",
            "currency": "EUR",
            "domicile": "Luxembourg",
            "inception_date": "2015-09-01",
            "target_nav_eur": target_nav,
        }

        with open(fund_dir / "fund_profile.json", "w") as f:
            json.dump(profile_data, f)

    loader = FundProfileLoader(temp_funds_dir)
    profiles = loader.load_all()

    assert len(profiles) == 2
    assert "UCITS_Balanced" in profiles
    assert "AIFM_HedgeFund" in profiles
    assert profiles["UCITS_Balanced"].fund_type == "UCITS"
    assert profiles["AIFM_HedgeFund"].fund_type == "AIFM"


def test_load_all_with_error(temp_funds_dir):
    """Test load_all when one fund has errors."""
    # Valid fund
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()
    with open(fund_dir / "fund_profile.json", "w") as f:
        json.dump(
            {
                "schema_version": "1.0",
                "fund_id": "UCITS_Balanced",
                "fund_name": "UCITS Balanced",
                "fund_type": "UCITS",
                "currency": "EUR",
                "domicile": "Luxembourg",
                "inception_date": "2015-09-01",
            },
            f,
        )

    # Invalid fund
    bad_dir = temp_funds_dir / "BadFund"
    bad_dir.mkdir()
    with open(bad_dir / "fund_profile.json", "w") as f:
        json.dump(
            {
                "schema_version": "1.0",
                "fund_id": "BadFund",
                "fund_type": "UCITS",
                "currency": "EUR",
                "domicile": "Luxembourg",
                "inception_date": "2015-09-01",
                # Missing fund_name
            },
            f,
        )

    loader = FundProfileLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="Failed to load some fund profiles"):
        loader.load_all()
