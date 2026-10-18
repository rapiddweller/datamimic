# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.catalog.guidance import GUIDANCE_DESCRIPTOR_ENV
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.PARSER_RESERVED_NAME,
        name="PARSER_RESERVED_NAME",
        title="Parser Reserved Name",
        template=(
            "Element <{element_tag}> name '{name}' is a reserved name (conflicts with registered "
            "generator/converter), please use another name"
        ),
        cause="An error occurred during descriptor parsing.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_INVALID_TAG,
        name="PARSER_INVALID_TAG",
        title="Parser Invalid Tag",
        template="Expect element tag name '{expected}', but got '{actual}'",
        cause="The configuration value is invalid for the descriptor parsing.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_NO_SUBELEMENTS_ALLOWED,
        name="PARSER_NO_SUBELEMENTS_ALLOWED",
        title="Parser No Subelements Allowed",
        template="Element <{element_tag}>{parent_clause} does not accept any sub-elements",
        cause="An error occurred during descriptor parsing.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_INVALID_CHILD,
        name="PARSER_INVALID_CHILD",
        title="Parser Invalid Child",
        template="Element <{element_tag}> got invalid child <{child_tag}>, expects: {expected}",
        cause="The configuration value is invalid for the descriptor parsing.",
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_VALIDATION_FAILED,
        name="PARSER_VALIDATION_FAILED",
        title="Parser Validation Failed",
        template="{details}",
        cause="An error occurred during descriptor parsing.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_ARRAY_SUBELEMENTS_NOT_ALLOWED,
        name="PARSER_ARRAY_SUBELEMENTS_NOT_ALLOWED",
        title="Parser Array Subelements Not Allowed",
        template="Element <array> '{name}' does not accept sub-elements unless type is '{data_type}'",
        cause="An error occurred during descriptor parsing.",
        resolution="Review the configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_ARRAY_LITERAL_EMPTY,
        name="PARSER_ARRAY_LITERAL_EMPTY",
        title="Parser Array Literal Empty",
        template="Literal array '{name}' must define at least one <value> element",
        cause=(
            "The configuration violates the requirement that Literal array '{name}' must define at"
            " least one<value>element."
        ),
        resolution="Provide a non-empty configuration and retry.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_ARRAY_VALUE_INVALID,
        name="PARSER_ARRAY_VALUE_INVALID",
        title="Parser Array Value Invalid",
        template=("Failed while parsing attributes of element <{child_tag}> inside <array> '{name}': {details}"),
        cause=(
            "The system failed while parsing attributes of element <{child_tag}> inside <array> '{name}': {details}."
        ),
        resolution="Correct the configuration to a valid value or configuration.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_EXECUTE_INVALID_SOURCE,
        name="PARSER_EXECUTE_INVALID_SOURCE",
        title="Parser Execute Invalid Source",
        template=(
            "<execute> requires exactly one code source: uri (a script file), inline text, or script (an expression)."
        ),
        cause=(
            "<execute> has no code source or combines uri, inline text, and script even though they are alternatives."
        ),
        resolution=("Provide exactly one source: uri= for a file, script= with type=, or an inline element body."),
    ),
    IssueDefinition(
        code=IssueCode.PARSER_EXECUTE_TYPE_UNRESOLVED,
        name="PARSER_EXECUTE_TYPE_UNRESOLVED",
        title="Parser Execute Type Unresolved",
        template=("<execute uri='{uri}'>: cannot infer execution type from the file extension; set an explicit type=."),
        cause="The <execute> uri has no recognised extension and no explicit type= was given.",
        resolution="Set type= (python, sql, or bash), or use a uri with a recognised extension.",
    ),
    IssueDefinition(
        code=IssueCode.PARSER_DESCRIPTOR_NOT_FOUND,
        name="PARSER_DESCRIPTOR_NOT_FOUND",
        title="Parser Descriptor Not Found",
        template="Descriptor file '{name}' not found in task workspace",
        cause="The referenced script could not be found for the descriptor parsing.",
        resolution="Ensure the referenced script exists and the identifier/path is correct.",
        guidance=GUIDANCE_DESCRIPTOR_ENV,
    ),
]
