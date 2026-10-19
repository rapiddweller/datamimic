# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.EXPORT_TARGET_NOT_FOUND,
        name="EXPORT_TARGET_NOT_FOUND",
        title="Export Target Not Found",
        template=("Target not found: {target}. Available exporters: {exporters}. Available clients: {clients}"),
        cause="The referenced target could not be found for the exporter configuration.",
        resolution="Ensure the referenced target exists and the identifier/path is correct.",
    ),
    IssueDefinition(
        code=IssueCode.EXPORT_TARGET_PARSE_FAILED,
        name="EXPORT_TARGET_PARSE_FAILED",
        title="Export Target Parse Failed",
        template="Failed to parse exporter target(s) '{targets}': {error}",
        cause="The system failed to parse exporter target(s) '{targets}': {error}.",
        resolution="Fix the input format and retry.",
    ),
    IssueDefinition(
        code=IssueCode.EXPORT_OPERATION_UNSUPPORTED,
        name="EXPORT_OPERATION_UNSUPPORTED",
        title="Export Operation Unsupported",
        template=("Unsupported operation '{operation}' for client '{client_name}'. Allowed operations: {allowed}"),
        cause=(
            "The configuration uses an unsupported operation '{operation}' for client "
            "'{client_name}'. Allowedoperations:{allowed}."
        ),
        resolution="Use a supported configuration or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.EXPORT_FLUSH_FAILED,
        name="EXPORT_FLUSH_FAILED",
        title="Export Flush Failed",
        template="Exporter flush failed: {detail}",
        cause="An exporter failed while flushing buffered records.",
        resolution="Inspect the reported exporter details and resolve the underlying target write error.",
    ),
]
