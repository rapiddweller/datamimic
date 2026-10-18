# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.catalog.guidance import GUIDANCE_PROJECT_ENV
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.INCLUDE_FILE_NOT_FOUND,
        name="INCLUDE_FILE_NOT_FOUND",
        title="Include File Not Found",
        template="Include file '{uri}' not found in task workspace",
        cause="The referenced configuration could not be found for the include configuration.",
        resolution="Ensure the referenced file exists and the identifier/path is correct.",
        guidance=GUIDANCE_PROJECT_ENV,
    ),
    IssueDefinition(
        code=IssueCode.INCLUDE_UNSUPPORTED_FILE_TYPE,
        name="INCLUDE_UNSUPPORTED_FILE_TYPE",
        title="Include Unsupported File Type",
        template="Unsupported include file type '{uri}'. Only .properties and .xml are supported",
        cause=(
            "The configuration uses an unsupported include file type '{uri}'. Only .properties and .xml are supported."
        ),
        resolution="Use a supported file or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.INCLUDE_UNSUPPORTED_FILE_TYPE_GENERATE,
        name="INCLUDE_UNSUPPORTED_FILE_TYPE_GENERATE",
        title="Include Unsupported File Type Generate",
        template="Unsupported include file type '{uri}' inside <generate>. Only .xml is supported",
        cause=(
            "The configuration uses an unsupported include file type '{uri}' inside <generate>. Only .xml is supported."
        ),
        resolution="Use a supported file or adjust the configuration.",
    ),
]
