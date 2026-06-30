"""Tests for RiskPolicyLoader."""

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from manco_risk.etl.reference_data.models import RiskPolicy
from manco_risk.etl.reference_data.risk_policy_loader import RiskPolicyLoader


@pytest.fixture
def temp_funds_dir():
    """Create a temporary funds directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_aifm_with_var_confidence(temp_funds_dir):
    """Test loading AIFM fund with var_framework.confidence_level."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "var_framework": {
            "use_var": True,
            "confidence_level": 0.99,
            "lookback_period_days": 250,
            "models": ["historical"],
        },
        "backtesting": {
            "use_backtesting": True,
            "observation_window": 250,
        },
        "stress_testing": {
            "most_relevant_historical_scenarios": {
                "source": "historical_scenarios",
                "selected_scenarios": ["2008", "2020", "2022"],
            }
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    policy = loader.load("AIFM_HedgeFund")

    assert isinstance(policy, RiskPolicy)
    assert policy.fund_id == "AIFM_HedgeFund"
    assert policy.var_confidence_level == Decimal("0.99")
    assert policy.var_lookback_days == 250
    assert policy.backtesting_window_days == 250
    assert policy.historical_scenario_names == ["2008", "2020", "2022"]


def test_load_ucits_without_var_confidence(temp_funds_dir):
    """Test loading UCITS fund without var_framework.confidence_level."""
    fund_dir = temp_funds_dir / "UCITS_Balanced"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "UCITS_Balanced",
        "var_framework": {
            "models": ["historical", "parametric"],
        },
        "backtesting": {
            "lookback_days": 250,
            "observation_window_months": 12,
        },
        "stress_testing": {
            "most_relevant_historical_scenarios": {
                "source": "scenario_library_2_historical",
                "selected_scenarios": [
                    "historical_2008_black_week",
                    "historical_2020_covid",
                    "historical_2022_rate_inflation",
                ],
            }
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    policy = loader.load("UCITS_Balanced")

    assert policy.fund_id == "UCITS_Balanced"
    assert policy.var_confidence_level is None
    assert policy.var_lookback_days == 250
    assert policy.backtesting_window_days == 12


def test_load_missing_file(temp_funds_dir):
    """Test error when policy file not found."""
    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="Risk policy not found"):
        loader.load("NonExistent")


def test_load_invalid_json(temp_funds_dir):
    """Test error when JSON is invalid."""
    fund_dir = temp_funds_dir / "BadJSON"
    fund_dir.mkdir()

    with open(fund_dir / "risk_policy.json", "w") as f:
        f.write("{invalid json}")

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="Invalid JSON"):
        loader.load("BadJSON")


def test_fund_id_mismatch(temp_funds_dir):
    """Test error when fund_id doesn't match folder."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "WrongId",
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="fund_id mismatch"):
        loader.load("AIFM_HedgeFund")


def test_invalid_var_confidence(temp_funds_dir):
    """Test error when var_confidence_level is not in (0, 1)."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "var_framework": {
            "confidence_level": 1.5,  # Invalid: outside (0, 1)
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="var_confidence_level must be decimal in"):
        loader.load("AIFM_HedgeFund")


def test_negative_var_lookback_days(temp_funds_dir):
    """Test error when var_lookback_days is negative."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "var_framework": {
            "lookback_period_days": -100,  # Invalid: negative
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="var_lookback_days.*must be positive"):
        loader.load("AIFM_HedgeFund")


def test_negative_backtesting_window(temp_funds_dir):
    """Test error when backtesting_window_days is negative."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "backtesting": {
            "observation_window": -50,  # Invalid: negative
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="backtesting_window_days.*must be positive"):
        loader.load("AIFM_HedgeFund")


def test_invalid_scenario_list(temp_funds_dir):
    """Test error when selected_scenarios is not a list."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "stress_testing": {
            "most_relevant_historical_scenarios": {
                "selected_scenarios": "2008",  # Not a list
            }
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    with pytest.raises(ValueError, match="selected_scenarios must be list"):
        loader.load("AIFM_HedgeFund")


def test_empty_scenario_names(temp_funds_dir):
    """Test that empty scenario list is treated as None."""
    fund_dir = temp_funds_dir / "AIFM_HedgeFund"
    fund_dir.mkdir()

    policy_data = {
        "schema_version": "1.0",
        "fund_id": "AIFM_HedgeFund",
        "stress_testing": {
            "most_relevant_historical_scenarios": {
                "selected_scenarios": [],  # Empty
            }
        },
    }

    with open(fund_dir / "risk_policy.json", "w") as f:
        json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    policy = loader.load("AIFM_HedgeFund")

    assert policy.historical_scenario_names is None


def test_load_all(temp_funds_dir):
    """Test loading all risk policies."""
    for fund_id in ["UCITS_Balanced", "AIFM_HedgeFund"]:
        fund_dir = temp_funds_dir / fund_id
        fund_dir.mkdir()

        policy_data = {
            "schema_version": "1.0",
            "fund_id": fund_id,
        }

        with open(fund_dir / "risk_policy.json", "w") as f:
            json.dump(policy_data, f)

    loader = RiskPolicyLoader(temp_funds_dir)
    policies = loader.load_all()

    assert len(policies) == 2
    assert "UCITS_Balanced" in policies
    assert "AIFM_HedgeFund" in policies
