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

from pathlib import Path

from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity
from datamimic_ce.authoring.domain.xml_diagnostics import Diagnostic
from datamimic_ce.errors import ParserValidationError

RULE_ENGINE_PARSE = "DM000"

# Client credentials are an execution concern; structural fields remain mandatory.
_CREDENTIAL_FIELDS = {"host", "port", "database", "user", "password"}


def _is_pure_credential_error(error: ValueError) -> bool:
    if not isinstance(error, ParserValidationError) or not error.validation_errors:
        return False
    for detail in error.validation_errors:
        location = detail.get("loc")
        if (
            detail.get("type") != "missing"
            or not isinstance(location, tuple | list)
            or len(location) != 1
            or location[0] not in _CREDENTIAL_FIELDS
        ):
            return False
    return True


def run_engine_parse(descriptor_path: Path) -> Diagnostic | None:
    """None when the engine accepts the descriptor, else one DM000 diagnostic."""
    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.engine.io.api import load_connection_profile

    try:
        from datamimic_ce.engine.runtime.api import runtime_environment

        DescriptorParser.parse(
            descriptor_path,
            None,
            runtime_environment(),
            profile_loader=load_connection_profile,
        )
    except (ValueError, FileNotFoundError) as err:
        if isinstance(err, ValueError) and _is_pure_credential_error(err):
            return None  # DB credentials are wired at run time, not a lint error
        return Diagnostic(
            rule=RULE_ENGINE_PARSE,
            severity=RuleSeverity.ERROR,
            message="Engine parser rejected the descriptor.",
            fix_hint="Correct the descriptor fields and workspace-local resource configuration.",
            element="setup",
            path="/setup",
        )
    return None
