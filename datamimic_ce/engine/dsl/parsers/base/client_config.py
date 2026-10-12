"""Credential attribute merging for database and MongoDB descriptor parsers."""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_ENVIRONMENT, ATTR_ID, ATTR_SYSTEM

logger = logging.getLogger("DATAMIMIC")

ConnectionProfileLoader = Callable[[Path, str], dict[str, str]]


def fulfill_credentials(
    descriptor_dir: Path,
    descriptor_attr: dict[str, str],
    env_props: dict[str, str] | dict[str, object] | None,
    system_type: str,
    runtime_environment: Literal["development", "production"],
    profile_loader: ConnectionProfileLoader,
) -> dict[str, object]:
    environment = (
        descriptor_attr.get(ATTR_ENVIRONMENT)
        or ("local" if runtime_environment == "development" else None)
        or "environment"
    )
    system = descriptor_attr.get(ATTR_SYSTEM)

    if system is None:
        if system_type in ["db", "mongo", "kafka", "dwh", "object-storage"]:
            system = descriptor_attr.get(ATTR_ID)
        else:
            raise ValueError(f"System type '{system_type}' is not supported")

    conf_props = env_props if env_props else {}
    if environment and system:
        conf_props.update(profile_loader(descriptor_dir, environment))

    credentials: dict[str, object] = dict(descriptor_attr)
    for attr_key, attr_value in conf_props.items():
        if attr_key.startswith(f"{system}.{system_type}.") and attr_value is not None:
            attr_name = "".join(attr_key.split(".")[2:])
            credentials[attr_name] = attr_value

            if any(pattern in attr_name.lower() for pattern in ["password", "pwd", "pass"]):
                logger.debug(f"Get value for {attr_name}: ******")
            else:
                logger.debug(f"Get value for {attr_name}: {attr_value}")

    return credentials
