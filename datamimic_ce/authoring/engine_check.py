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

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity

RULE_ENGINE_PARSE = "DM000"


def run_engine_parse(descriptor_path: Path) -> Diagnostic | None:
    """None when the engine accepts the descriptor, else one DM000 diagnostic."""
    from datamimic_ce.parsers.descriptor_parser import DescriptorParser

    try:
        DescriptorParser.parse(descriptor_path, None)
    except (ValueError, FileNotFoundError) as err:
        return Diagnostic(
            rule=RULE_ENGINE_PARSE,
            severity=Severity.ERROR,
            message=f"Engine parser rejected the descriptor: {err}",
            fix_hint="Fix the reported element/attribute; the message quotes the engine's own check.",
            element="setup",
            path="/setup",
        )
    return None
