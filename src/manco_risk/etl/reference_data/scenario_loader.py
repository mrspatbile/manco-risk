"""Loader for historical scenarios (historical_scenarios.json).

Responsibilities:
- Load historical_scenarios.json from data/reference/
- Validate shock parameters
- Return HistoricalScenarios typed object with scenario lookup
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from manco_risk.etl.reference_data.models import (
    HistoricalScenario,
    HistoricalScenarios,
)


class HistoricalScenarioLoader:
    """Load and validate historical scenarios from historical_scenarios.json."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        """Initialize loader with data root directory.

        Parameters
        ----------
        data_root : Path, optional
            Root directory containing reference/ folder. Defaults to data/reference/
        """
        if data_root is None:
            data_root = Path("data/reference")
        self.data_root = Path(data_root)

    def load(self) -> HistoricalScenarios:
        """Load and validate all historical scenarios.

        Returns
        -------
        HistoricalScenarios
            Container with all validated scenarios

        Raises
        ------
        ValueError
            If file not found, parsing fails, or validation fails
        """
        scenarios_path = self.data_root / "historical_scenarios.json"

        if not scenarios_path.exists():
            raise ValueError(f"Scenarios file not found: {scenarios_path}")

        try:
            with open(scenarios_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {scenarios_path}: {e}") from e
        except IOError as e:
            raise ValueError(f"Cannot read {scenarios_path}: {e}") from e

        try:
            schema_version = data.get("schema_version", "")
            if not schema_version:
                raise ValueError("schema_version is required")

            # Extract scenario objects
            scenarios_dict: Dict[str, HistoricalScenario] = {}
            errors: Dict[str, str] = {}

            for scenario_id, scenario_data in data.items():
                if scenario_id == "schema_version":
                    continue

                try:
                    scenario = self._parse_scenario(scenario_id, scenario_data)
                    scenarios_dict[scenario_id] = scenario
                except ValueError as e:
                    errors[scenario_id] = str(e)

            if errors:
                error_msg = "\n".join(f"  {sid}: {err}" for sid, err in errors.items())
                raise ValueError(f"Failed to parse some scenarios:\n{error_msg}")

            # Build HistoricalScenarios container
            hist_scenarios = HistoricalScenarios(
                schema_version=schema_version, scenarios=scenarios_dict
            )
            return hist_scenarios

        except ValueError:
            raise
        except ValidationError as e:
            raise ValueError(f"Scenarios validation failed: {e}") from e

    def _parse_scenario(self, scenario_id: str, scenario_data: Any) -> HistoricalScenario:
        """Parse and validate a single scenario.

        Parameters
        ----------
        scenario_id : str
            Scenario key from JSON (e.g., "2008")
        scenario_data : dict
            Scenario object from JSON

        Returns
        -------
        HistoricalScenario
            Validated scenario object

        Raises
        ------
        ValueError
            If any field is invalid
        """
        if not isinstance(scenario_data, dict):
            raise ValueError(f"Scenario {scenario_id} must be object, got: {type(scenario_data)}")

        # Extract and validate name
        name = scenario_data.get("name", "").strip()
        if not name:
            raise ValueError(f"Scenario {scenario_id}: name is required and non-empty")

        # Extract and validate description
        description = scenario_data.get("description", "").strip()
        if not description:
            raise ValueError(f"Scenario {scenario_id}: description is required and non-empty")

        # Parse shock parameters (Decimal)
        try:
            delta_equity = Decimal(str(scenario_data.get("delta_equity", 0)))
            delta_y = Decimal(str(scenario_data.get("delta_y", 0)))
            delta_spread = Decimal(str(scenario_data.get("delta_spread", 0)))
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValueError(f"Scenario {scenario_id}: shock parameters must be numbers") from e

        # Parse FX shocks
        fx_shocks_raw = scenario_data.get("fx_shocks", {})
        if not isinstance(fx_shocks_raw, dict):
            raise ValueError(
                f"Scenario {scenario_id}: fx_shocks must be object, got: {type(fx_shocks_raw)}"
            )

        fx_shocks: Dict[str, Decimal] = {}
        try:
            for currency, shock in fx_shocks_raw.items():
                fx_shocks[currency] = Decimal(str(shock))
        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValueError(f"Scenario {scenario_id}: fx_shocks values must be numbers") from e

        return HistoricalScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            delta_equity=delta_equity,
            delta_y=delta_y,
            delta_spread=delta_spread,
            fx_shocks=fx_shocks,
        )

    def get_scenario(self, scenarios: HistoricalScenarios, scenario_id: str) -> HistoricalScenario:
        """Retrieve a specific scenario by ID.

        Parameters
        ----------
        scenarios : HistoricalScenarios
            Container of scenarios (from load())
        scenario_id : str
            Scenario ID to retrieve (e.g., "2008")

        Returns
        -------
        HistoricalScenario
            The requested scenario

        Raises
        ------
        ValueError
            If scenario ID not found
        """
        if scenario_id not in scenarios.scenarios:
            available = list(scenarios.scenarios.keys())
            raise ValueError(f"Scenario {scenario_id!r} not found. Available: {available}")
        return scenarios.scenarios[scenario_id]

    def validate_scenario_references(
        self, scenarios: HistoricalScenarios, scenario_ids: list[str]
    ) -> None:
        """Validate that all referenced scenario IDs exist.

        Parameters
        ----------
        scenarios : HistoricalScenarios
            Container of scenarios (from load())
        scenario_ids : list[str]
            List of scenario IDs to validate

        Raises
        ------
        ValueError
            If any scenario ID not found
        """
        missing = [sid for sid in scenario_ids if sid not in scenarios.scenarios]
        if missing:
            available = list(scenarios.scenarios.keys())
            raise ValueError(f"Missing scenarios: {missing}. Available: {available}")
