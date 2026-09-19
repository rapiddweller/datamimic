# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Authoring toolkit for the DATAMIMIC DSL: linter, dry-run, and reference.

Consumed by the CLI (``datamimic lint``) and the MCP tools (``datamimic_check``,
``datamimic_run``, ``datamimic_reference``). Must not import fastmcp — the base
install is enough.
"""

from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult, Severity
from datamimic_ce.authoring.linter import lint_descriptor, lint_source

__all__ = [
    "Diagnostic",
    "LintResult",
    "Severity",
    "lint_descriptor",
    "lint_source",
]
