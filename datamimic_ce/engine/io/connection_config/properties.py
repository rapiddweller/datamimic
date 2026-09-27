"""Load connection profiles from the existing CE properties locations."""

import logging
import os
from pathlib import Path

from datamimic_ce.engine.dsl.api import parse_properties

logger = logging.getLogger("DATAMIMIC")


def load_connection_profile(descriptor_dir: Path, environment: str) -> dict[str, str]:
    """Load one profile using descriptor, current-directory, then home fallback."""
    profile_name = f"{environment}.env.properties"
    try:
        profile = parse_properties(descriptor_dir / "conf" / profile_name)
        return profile
    except FileNotFoundError:
        logger.info(f"Environment file not found {descriptor_dir / 'conf' / profile_name}")

    try:
        profile = parse_properties(Path(profile_name))
        logger.info(f"Environment file found in current directory: {profile_name}")
        return profile
    except FileNotFoundError:
        logger.info(f"Environment file not found in current directory: {profile_name}")

    try:
        home_dir = os.path.expanduser("~")
        profile = parse_properties(Path(home_dir) / "datamimic" / profile_name)
        logger.info(f"Environment file found in home directory: ~/datamimic/{profile_name}")
        return profile
    except FileNotFoundError:
        logger.info(f"Environment file not found in home directory: ~/datamimic/{profile_name}")
        return {}
