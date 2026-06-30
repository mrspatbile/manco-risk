"""Loader for fund profiles (fund_profile.json).

Responsibilities:
- Load fund_profile.json from data/funds/{fund_id}/
- Validate required fields
- Return FundProfile typed object
"""

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from manco_risk.etl.reference_data.models import FundProfile


class FundProfileLoader:
    """Load and validate fund profiles from fund_profile.json."""

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

    def load(self, fund_id: str) -> FundProfile:
        """Load and validate fund profile for a specific fund.

        Parameters
        ----------
        fund_id : str
            Fund identifier (folder name, e.g., "UCITS_Balanced")

        Returns
        -------
        FundProfile
            Validated fund profile

        Raises
        ------
        ValueError
            If file not found, parsing fails, or validation fails
        """
        profile_path = self.data_root / fund_id / "fund_profile.json"

        if not profile_path.exists():
            raise ValueError(f"Fund profile not found: {profile_path}")

        try:
            with open(profile_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {profile_path}: {e}") from e
        except IOError as e:
            raise ValueError(f"Cannot read {profile_path}: {e}") from e

        # Validate fund_id matches folder name
        if data.get("fund_id") != fund_id:
            raise ValueError(
                f"fund_id mismatch: folder={fund_id}, JSON fund_id={data.get('fund_id')}"
            )

        # Extract and validate fields
        try:
            schema_version = data.get("schema_version", "")
            if not schema_version:
                raise ValueError("schema_version is required")

            fund_name = data.get("fund_name", "").strip()
            if not fund_name:
                raise ValueError("fund_name is required and must be non-empty")

            fund_type = data.get("fund_type", "").strip()
            if not fund_type:
                raise ValueError("fund_type is required and must be non-empty")

            currency = data.get("currency", "").strip()
            if not currency:
                raise ValueError("currency is required and must be non-empty")
            if len(currency) != 3:
                raise ValueError(f"currency must be 3-letter ISO code, got: {currency}")

            domicile = data.get("domicile", "").strip()
            if not domicile:
                raise ValueError("domicile is required and must be non-empty")

            # Parse inception date
            inception_date_str = data.get("inception_date", "")
            if not inception_date_str:
                raise ValueError("inception_date is required")
            try:
                inception_date = date.fromisoformat(inception_date_str)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"inception_date must be ISO 8601 date (YYYY-MM-DD), got: {inception_date_str}"
                ) from e

            # Validate inception_date is not in future
            if inception_date > date.today():
                raise ValueError(f"inception_date cannot be in future: {inception_date}")

            # Parse target_nav_eur (optional)
            target_nav_eur: Optional[Decimal] = None
            if "target_nav_eur" in data and data["target_nav_eur"] is not None:
                try:
                    target_nav_eur = Decimal(str(data["target_nav_eur"]))
                    if target_nav_eur <= 0:
                        raise ValueError(f"target_nav_eur must be positive, got: {target_nav_eur}")
                except (InvalidOperation, ValueError) as e:
                    raise ValueError(
                        f"target_nav_eur must be a positive number, got: {data['target_nav_eur']}"
                    ) from e

            # Build FundProfile
            profile = FundProfile(
                schema_version=schema_version,
                fund_id=fund_id,
                fund_name=fund_name,
                fund_type=fund_type,
                currency=currency,
                domicile=domicile,
                inception_date=inception_date,
                target_nav_eur=target_nav_eur,
                fund_short_name=data.get("fund_short_name"),
                strategy=data.get("strategy"),
                regulator=data.get("regulator"),
            )
            return profile

        except ValueError:
            raise
        except ValidationError as e:
            raise ValueError(f"Profile validation failed: {e}") from e

    def load_all(self) -> dict[str, FundProfile]:
        """Load all fund profiles from data/funds/.

        Returns
        -------
        dict[str, FundProfile]
            Mapping of fund_id to FundProfile

        Raises
        ------
        ValueError
            If any fund profile fails to load
        """
        if not self.data_root.exists():
            raise ValueError(f"Data root not found: {self.data_root}")

        profiles: dict[str, FundProfile] = {}
        errors: dict[str, str] = {}

        for fund_dir in sorted(self.data_root.iterdir()):
            if not fund_dir.is_dir():
                continue

            fund_id = fund_dir.name
            try:
                profile = self.load(fund_id)
                profiles[fund_id] = profile
            except ValueError as e:
                errors[fund_id] = str(e)

        if errors:
            error_msg = "\n".join(f"  {fid}: {err}" for fid, err in errors.items())
            raise ValueError(f"Failed to load some fund profiles:\n{error_msg}")

        return profiles
