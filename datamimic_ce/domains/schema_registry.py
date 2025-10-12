from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator  # type: ignore[import-untyped]

from .exceptions import DomainError

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


@cache
def load_schema(domain: str, kind: str, version: str) -> Draft7Validator:
    filename = f"{domain}.{version}.{kind}.json"
    path = SCHEMA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing schema file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return Draft7Validator(schema)


def validate_payload(
    payload: dict[str, Any],
    domain: str,
    kind: str,
    version: str,
    request_hash: str,
) -> None:
    validator = load_schema(domain, kind, version)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        raise DomainError(
            code="schema_validation_failed",
            message=f"{kind.capitalize()} schema validation failed for {domain} {version}",
            hint="Check the payload against the domain contract.",
            path="/" + "/".join(str(part) for part in errors[0].absolute_path),
            request_hash=request_hash,
            details={
                "errors": [
                    {
                        "message": error.message,
                        "path": list(error.absolute_path),
                    }
                    for error in errors
                ]
            },
        )
