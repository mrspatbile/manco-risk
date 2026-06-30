"""Loader for risk policies (risk_policy.json).

Responsibilities:
- Load risk_policy.json from data/funds/{fund_id}/
- Extract key VaR and backtesting parameters
- Handle field name variations (UCITS vs AIFM)
- Validate extracted parameters
- Return RiskPolicy typed object
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from manco_risk.etl.reference_data.models import RiskPolicy


class RiskPolicyLoader:
    """Load and validate risk policies from risk_policy.json."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        """Initialize loader with data root directory.

        Parameters
        ----------
        data_root : Path, optional
            Root directory containing funds/ folder. Defaults to data/funds/
        """
        if data_root is None:
            data_root = Path("data/funds")
        self.data_root = Path(data_root)

    def load(self, fund_id: str) -> RiskPolicy:
        """Load and validate risk policy for a specific fund.

        Parameters
        ----------
        fund_id : str
            Fund identifier (folder name, e.g., "UCITS_Balanced")

        Returns
        -------
        RiskPolicy
            Validated risk policy

        Raises
        ------
        ValueError
            If file not found, parsing fails, or validation fails
        """
        policy_path = self.data_root / fund_id / "risk_policy.json"

        if not policy_path.exists():
            raise ValueError(f"Risk policy not found: {policy_path}")

        try:
            with open(policy_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {policy_path}: {e}") from e
        except IOError as e:
            raise ValueError(f"Cannot read {policy_path}: {e}") from e

        # Validate fund_id matches folder name
        if data.get("fund_id") != fund_id:
            raise ValueError(
                f"fund_id mismatch: folder={fund_id}, JSON fund_id={data.get('fund_id')}"
            )

        try:
            schema_version = data.get("schema_version", "")
            if not schema_version:
                raise ValueError("schema_version is required")

            # Extract VaR confidence level (optional; only AIFM has it)
            var_confidence_level: Optional[Decimal] = None
            var_framework = data.get("var_framework")
            if var_framework and isinstance(var_framework, dict):
                conf_level = var_framework.get("confidence_level")
                if conf_level is not None:
                    try:
                        var_confidence_level = Decimal(str(conf_level))
                        if not (Decimal(0) < var_confidence_level < Decimal(1)):
                            raise ValueError(
                                f"var_confidence_level must be in (0, 1), got: {var_confidence_level}"
                            )
                    except (InvalidOperation, ValueError) as e:
                        raise ValueError(
                            f"var_confidence_level must be decimal in (0, 1), got: {conf_level}"
                        ) from e

            # Extract VaR lookback period (try multiple field names)
            var_lookback_days: Optional[int] = None
            if var_framework and isinstance(var_framework, dict):
                lookback = var_framework.get("lookback_period_days")
                if lookback is not None:
                    try:
                        var_lookback_days = int(lookback)
                        if var_lookback_days <= 0:
                            raise ValueError(
                                f"var_lookback_days must be positive, got: {var_lookback_days}"
                            )
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"var_lookback_days (from var_framework.lookback_period_days) must be positive integer, got: {lookback}"
                        ) from e

            # Fallback: try backtesting.lookback_days (UCITS)
            if var_lookback_days is None:
                backtesting = data.get("backtesting")
                if backtesting and isinstance(backtesting, dict):
                    lookback = backtesting.get("lookback_days")
                    if lookback is not None:
                        try:
                            var_lookback_days = int(lookback)
                            if var_lookback_days <= 0:
                                raise ValueError(
                                    f"var_lookback_days must be positive, got: {var_lookback_days}"
                                )
                        except (ValueError, TypeError) as e:
                            raise ValueError(
                                f"var_lookback_days (from backtesting.lookback_days) must be positive integer, got: {lookback}"
                            ) from e

            # Extract backtesting window (try multiple field names)
            backtesting_window_days: Optional[int] = None
            backtesting = data.get("backtesting")
            if backtesting and isinstance(backtesting, dict):
                window = backtesting.get("observation_window")
                if window is not None:
                    try:
                        backtesting_window_days = int(window)
                        if backtesting_window_days <= 0:
                            raise ValueError(
                                f"backtesting_window_days must be positive, got: {backtesting_window_days}"
                            )
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"backtesting_window_days (from backtesting.observation_window) must be positive integer, got: {window}"
                        ) from e

            # Fallback: try backtesting.observation_window_months (UCITS)
            if backtesting_window_days is None and backtesting:
                window_months = backtesting.get("observation_window_months")
                if window_months is not None:
                    try:
                        backtesting_window_days = int(window_months)
                        if backtesting_window_days <= 0:
                            raise ValueError(
                                f"backtesting_window_days must be positive, got: {backtesting_window_days}"
                            )
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"backtesting_window_days (from backtesting.observation_window_months) must be positive integer, got: {window_months}"
                        ) from e

            # Extract historical scenario names
            historical_scenario_names: Optional[list[str]] = None
            stress_testing = data.get("stress_testing")
            if stress_testing and isinstance(stress_testing, dict):
                most_relevant = stress_testing.get("most_relevant_historical_scenarios")
                if most_relevant and isinstance(most_relevant, dict):
                    scenarios = most_relevant.get("selected_scenarios")
                    if scenarios:
                        if not isinstance(scenarios, list):
                            raise ValueError(
                                f"selected_scenarios must be list, got: {type(scenarios)}"
                            )
                        if not all(isinstance(s, str) for s in scenarios):
                            raise ValueError("selected_scenarios must contain only strings")
                        if scenarios:  # Only set if non-empty
                            historical_scenario_names = scenarios

            # Build RiskPolicy
            policy = RiskPolicy(
                schema_version=schema_version,
                fund_id=fund_id,
                var_confidence_level=var_confidence_level,
                var_lookback_days=var_lookback_days,
                backtesting_window_days=backtesting_window_days,
                historical_scenario_names=historical_scenario_names,
            )
            return policy

        except ValueError:
            raise
        except ValidationError as e:
            raise ValueError(f"Policy validation failed: {e}") from e

    def load_all(self) -> dict[str, RiskPolicy]:
        """Load all risk policies from data/funds/.

        Returns
        -------
        dict[str, RiskPolicy]
            Mapping of fund_id to RiskPolicy

        Raises
        ------
        ValueError
            If any risk policy fails to load
        """
        if not self.data_root.exists():
            raise ValueError(f"Data root not found: {self.data_root}")

        policies: dict[str, RiskPolicy] = {}
        errors: dict[str, str] = {}

        for fund_dir in sorted(self.data_root.iterdir()):
            if not fund_dir.is_dir():
                continue

            fund_id = fund_dir.name
            try:
                policy = self.load(fund_id)
                policies[fund_id] = policy
            except ValueError as e:
                errors[fund_id] = str(e)

        if errors:
            error_msg = "\n".join(f"  {fid}: {err}" for fid, err in errors.items())
            raise ValueError(f"Failed to load some risk policies:\n{error_msg}")

        return policies
