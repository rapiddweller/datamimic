"""Canonical public API for DATAMIMIC intent authoring."""

from datamimic_ce.authoring.contracts import ScaffoldRequest, ScaffoldResult
from datamimic_ce.authoring.service import scaffold
from datamimic_ce.authoring.spec import AuthoringSpecV1, authoring_spec_json_schema

__all__ = [
    "AuthoringSpecV1",
    "ScaffoldRequest",
    "ScaffoldResult",
    "authoring_spec_json_schema",
    "scaffold",
]
