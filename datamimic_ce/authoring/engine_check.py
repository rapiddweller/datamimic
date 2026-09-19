# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Phase 2 of the linter: the engine's own parser as final authority.

DescriptorParser.parse runs the full parser dispatch + Pydantic + nesting +
cross-field validation without generating anything. It is fail-fast (first
ValueError wins), so it only runs when phase 1 found no errors — anything it
still catches becomes a DM000 diagnostic (a lint rule gap worth closing)."""

import re
from pathlib import Path

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity

RULE_ENGINE_PARSE = "DM000"

# The engine resolves <database>/<mongodb> credentials AT PARSE TIME from
# conf/{env}.env.properties. That is an environment concern, not descriptor
# validity — the linter has no conf and must not fail a structurally-correct
# DB descriptor on it (dry-run surfaces real connectivity as DM002 instead).
# But a MISSING STRUCTURAL attribute (e.g. <database> without dbms) shares the
# same top-level message, so suppress only when every missing field is a credential.
_CREDENTIAL_SIGNATURE = "make sure all required attributes are provided"
_CREDENTIAL_FIELDS = {"host", "port", "database", "user", "password"}
_MISSING_FIELD = re.compile(r"-\s*(\w+):\s*Field required")


def _is_pure_credential_error(message: str) -> bool:
    if _CREDENTIAL_SIGNATURE not in message:
        return False
    missing = set(_MISSING_FIELD.findall(message))
    return bool(missing) and missing <= _CREDENTIAL_FIELDS


def run_engine_parse(descriptor_path: Path) -> Diagnostic | None:
    """None when the engine accepts the descriptor, else one DM000 diagnostic."""
    from datamimic_ce.parsers.descriptor_parser import DescriptorParser

    try:
        DescriptorParser.parse(descriptor_path, None)
    except (ValueError, FileNotFoundError) as err:
        if _is_pure_credential_error(str(err)):
            return None  # DB credentials are wired at run time, not a lint error
        return Diagnostic(
            rule=RULE_ENGINE_PARSE,
            severity=Severity.ERROR,
            message=f"Engine parser rejected the descriptor: {err}",
            fix_hint="Fix the reported element/attribute; the message quotes the engine's own check.",
            element="setup",
            path="/setup",
        )
    return None
