"""Validated run-scoped key input for Hash converters."""

from __future__ import annotations

import base64
import binascii
import os
from dataclasses import dataclass, field

from datamimic_ce.errors import IssueCode, RuntimeConfigError, runtime_config_error


def _invalid(reason: str) -> RuntimeConfigError:
    return runtime_config_error(code=IssueCode.RUNTIME_PSEUDONYMIZATION_KEY_INVALID, reason=reason)


@dataclass(frozen=True, slots=True, repr=False)
class PseudonymizationKey:
    value: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.value) is not bytes or len(self.value) < 32:
            raise _invalid("pseudonymization key must contain at least 32 bytes")

    def __repr__(self) -> str:
        return "PseudonymizationKey(<redacted>)"


def resolve_pseudonymization_key(
    platform_config: dict[str, object] | None, supplied: PseudonymizationKey | None
) -> PseudonymizationKey | None:
    config = {} if platform_config is None else platform_config
    env_name = config.get("pseudonymization_key_env")
    if env_name is not None and not isinstance(env_name, str):
        raise _invalid("pseudonymization_key_env must be a string")
    if env_name is not None and (not env_name or env_name != env_name.strip()):
        raise _invalid("pseudonymization_key_env must name an environment variable")
    if supplied is not None and env_name is not None:
        raise _invalid("provide either pseudonymization_key_env or a typed key, not both")
    if supplied is not None:
        return supplied
    if env_name is None:
        return None
    encoded = os.environ.get(env_name)
    if encoded is None:
        raise _invalid("referenced environment variable is not set")
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise _invalid("referenced environment variable must contain strict standard Base64") from None
    return PseudonymizationKey(decoded)
