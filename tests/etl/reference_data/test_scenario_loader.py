"""Tests for HistoricalScenarioLoader."""

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from manco_risk.etl.reference_data.models import HistoricalScenarios
from manco_risk.etl.reference_data.scenario_loader import HistoricalScenarioLoader


@pytest.fixture
def temp_ref_dir():
    """Create a temporary reference data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_scenarios(temp_ref_dir):
    """Test loading all historical scenarios."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {"USD": -0.05, "GBP": -0.15},
        },
        "2020": {
            "name": "Covid 2020",
            "description": "Pandemic shock",
            "delta_equity": -0.3,
            "delta_y": -0.005,
            "delta_spread": 0.02,
            "fx_shocks": {"USD": 0.05, "GBP": -0.05},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    scenarios = loader.load()

    assert isinstance(scenarios, HistoricalScenarios)
    assert scenarios.schema_version == "1.0"
    assert len(scenarios.scenarios) == 2
    assert "2008" in scenarios.scenarios
    assert "2020" in scenarios.scenarios

    scenario_2008 = scenarios.scenarios["2008"]
    assert scenario_2008.scenario_id == "2008"
    assert scenario_2008.name == "GFC 2008"
    assert scenario_2008.delta_equity == Decimal("-0.4")
    assert scenario_2008.delta_y == Decimal("-0.01")
    assert scenario_2008.fx_shocks["USD"] == Decimal("-0.05")


def test_load_missing_file(temp_ref_dir):
    """Test error when scenarios file not found."""
    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="Scenarios file not found"):
        loader.load()


def test_load_invalid_json(temp_ref_dir):
    """Test error when JSON is invalid."""
    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        f.write("{invalid json}")

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="Invalid JSON"):
        loader.load()


def test_missing_schema_version(temp_ref_dir):
    """Test error when schema_version is missing."""
    scenarios_data = {
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        }
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="schema_version is required"):
        loader.load()


def test_missing_scenario_name(temp_ref_dir):
    """Test error when scenario name is missing."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="name is required"):
        loader.load()


def test_missing_scenario_description(temp_ref_dir):
    """Test error when scenario description is missing."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="description is required"):
        loader.load()


def test_invalid_shock_type(temp_ref_dir):
    """Test error when shock parameter is not a number."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": "invalid",  # Not a number
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="shock parameters must be numbers"):
        loader.load()


def test_invalid_fx_shock_type(temp_ref_dir):
    """Test error when fx_shocks is not a dict."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": "invalid",  # Not a dict
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="fx_shocks must be object"):
        loader.load()


def test_invalid_fx_shock_value(temp_ref_dir):
    """Test error when fx_shocks value is not a number."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {"USD": "invalid"},  # Invalid shock value
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    with pytest.raises(ValueError, match="fx_shocks values must be numbers"):
        loader.load()


def test_get_scenario(temp_ref_dir):
    """Test retrieving a specific scenario."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    scenarios = loader.load()

    scenario = loader.get_scenario(scenarios, "2008")
    assert scenario.scenario_id == "2008"
    assert scenario.name == "GFC 2008"


def test_get_scenario_not_found(temp_ref_dir):
    """Test error when retrieving non-existent scenario."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    scenarios = loader.load()

    with pytest.raises(ValueError, match="Scenario '2020' not found"):
        loader.get_scenario(scenarios, "2020")


def test_validate_scenario_references(temp_ref_dir):
    """Test validating scenario references."""
    scenarios_data = {
        "schema_version": "1.0",
        "2008": {
            "name": "GFC 2008",
            "description": "Global Financial Crisis",
            "delta_equity": -0.4,
            "delta_y": -0.01,
            "delta_spread": 0.03,
            "fx_shocks": {},
        },
        "2020": {
            "name": "Covid 2020",
            "description": "Pandemic shock",
            "delta_equity": -0.3,
            "delta_y": -0.005,
            "delta_spread": 0.02,
            "fx_shocks": {},
        },
    }

    with open(temp_ref_dir / "historical_scenarios.json", "w") as f:
        json.dump(scenarios_data, f)

    loader = HistoricalScenarioLoader(temp_ref_dir)
    scenarios = loader.load()

    # Valid references
    loader.validate_scenario_references(scenarios, ["2008", "2020"])

    # Invalid reference
    with pytest.raises(ValueError, match="Missing scenarios"):
        loader.validate_scenario_references(scenarios, ["2008", "2099"])
