# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.catalog.guidance import GUIDANCE_PROJECT_ENV
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.SOURCE_INVALID_CSV,
        name="SOURCE_INVALID_CSV",
        title="Source Invalid CSV",
        template="Invalid CSV in '{name}'",
        cause="The CSV file content is malformed or cannot be parsed.",
        resolution="Fix CSV syntax, delimiter, and quoting, then retry.",
        guidance=GUIDANCE_PROJECT_ENV,
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_INVALID_JSON,
        name="SOURCE_INVALID_JSON",
        title="Source Invalid JSON",
        template="Invalid JSON in '{name}'",
        cause="The JSON file content is malformed or cannot be parsed.",
        resolution="Fix JSON syntax and ensure the file is valid JSON.",
        guidance=GUIDANCE_PROJECT_ENV,
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_JSON_ROOT_INVALID,
        name="SOURCE_JSON_ROOT_INVALID",
        title="Source JSON Root Invalid",
        template="JSON file '{name}' must contain a list of objects or a dictionary",
        cause="The JSON root value is not a list of objects or a dictionary.",
        resolution="Use a JSON array of objects or a dictionary at the root.",
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_XML_ROOT_INVALID,
        name="SOURCE_XML_ROOT_INVALID",
        title="Source XML Root Invalid",
        template="XML file '{name}' must contain a dictionary",
        cause="The XML root does not map to a dictionary structure.",
        resolution="Ensure the XML root maps to key/value structure expected by the loader.",
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_UNSUPPORTED_FILE_TYPE,
        name="SOURCE_UNSUPPORTED_FILE_TYPE",
        title="Source Unsupported File Type",
        template="Data source '{name}' is not supported by DataSourceRegistry",
        cause="The source configuration specifies an unsupported configuration.",
        resolution="Use a supported file or adjust the configuration.",
        guidance=GUIDANCE_PROJECT_ENV,
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_EXPR_NESTED_NOT_STRING,
        name="SOURCE_EXPR_NESTED_NOT_STRING",
        title="Source Expr Nested Not String",
        template="NestedKey source expression must evaluate to a string",
        cause=(
            "The configuration violates the requirement that NestedKey source expression must evaluate to a string."
        ),
        resolution="Set the source to a string value.",
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_CLIENT_UNSUPPORTED,
        name="SOURCE_CLIENT_UNSUPPORTED",
        title="Source Client Unsupported",
        template="Cannot load data from client: {client_type}",
        cause="The system could not load data from client: {client_type}.",
        resolution="Use a supported client or adjust the configuration.",
    ),
    IssueDefinition(
        code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
        name="SOURCE_MONGO_SELECTOR_INVALID",
        title="Source Mongo Selector Invalid",
        template="Invalid Mongo selector: {error}",
        cause="The configuration provides an invalid Mongo selector: {error}.",
        resolution="Correct the Mongo selector to a valid value or configuration.",
    ),
]
