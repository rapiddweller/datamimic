# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.CLIENT_PREFLIGHT_INVALID_CONFIGURATION,
        name="CLIENT_PREFLIGHT_INVALID_CONFIGURATION",
        title="Client Preflight Invalid Configuration",
        template="Client preflight failed for '{client_id}' ({kind}): {reason}",
        cause="The connection configuration failed validation before connectivity checks.",
        resolution="Fix the configuration values and retry.",
    ),
    IssueDefinition(
        code=IssueCode.CLIENT_SYSTEM_TYPE_UNSUPPORTED,
        name="CLIENT_SYSTEM_TYPE_UNSUPPORTED",
        title="Client System Type Unsupported",
        template="System type '{system_type}' is not supported",
        cause="The client/runtime configuration specifies an unsupported client.",
        resolution="Use a supported client or adjust the configuration.",
    ),
]
