# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.OPERATION_EXECUTION_FAILED,
        name="OPERATION_EXECUTION_FAILED",
        title="Operation Execution Failed",
        template="Operation '{target}' failed: {error}",
        cause="An error occurred during operation execution.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED,
        name="OPERATION_READ_ONLY_WRITE_BLOCKED",
        title="Operation Read-Only Write Blocked",
        template="Operation '{target}' blocked by read-only datasource mode: {reason}",
        cause="A write operation was attempted against a datasource configured for read-only access.",
        resolution="Disable read-only mode or use a writable datasource for update/delete/insert operations.",
    ),
    IssueDefinition(
        code=IssueCode.OPERATION_INTENT_INVALID,
        name="OPERATION_INTENT_INVALID",
        title="Database Operation Intent Is Invalid",
        template="Operation '{target}' is unsafe or ambiguous: {reason}. Migration: {migration}",
        cause=(
            "The descriptor does not distinguish selective deletion, clearing records, and dropping the "
            "database object strongly enough for a destructive operation."
        ),
        resolution="Use the explicit delete, clear, or drop target described in the migration guidance.",
    ),
]
