# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode, IssueSeverity

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED,
        name="ECHO_PLACEHOLDER_UNRESOLVED",
        title="Echo Placeholder Unresolved",
        template=(
            "<echo>: could not evaluate diagnostic placeholder text '{value}'{error_clause}; "
            "logging the literal text instead."
        ),
        cause=("The echo text referenced a name or expression that is not available in the current runtime scope."),
        resolution="Fix the placeholder expression, or remove it if the echo is only diagnostic output.",
        severity=IssueSeverity.WARNING,
    ),
]
