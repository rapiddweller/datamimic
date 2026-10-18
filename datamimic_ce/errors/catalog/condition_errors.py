# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.CONDITION_DUPLICATE_IF,
        name="CONDITION_DUPLICATE_IF",
        title="Condition Duplicate If",
        template="Fail while parsing <condition>. Only one tag <if> is allowed in <condition>.",
        cause=("A <condition> block contains more than one first <if> branch, so branch order is ambiguous."),
        resolution=("Keep exactly one <if> as the first child; add further conditions as <else-if> children."),
    ),
    IssueDefinition(
        code=IssueCode.CONDITION_IF_MISSING,
        name="CONDITION_IF_MISSING",
        title="Condition If Missing",
        template="Fail while parsing <condition>. Must have <if> as the first tag.",
        cause="A <condition> block has no initial <if> branch to establish the first decision.",
        resolution='Add exactly one <if condition="..."> as the first child.',
    ),
    IssueDefinition(
        code=IssueCode.CONDITION_ELSE_AFTER,
        name="CONDITION_ELSE_AFTER",
        title="Condition Else After",
        template="Fail while parsing <condition>. Tag <else> must be the last tag.",
        cause=("An <else> branch is followed by another branch, but <else> is the unconditional final fallback."),
        resolution="Move <else> after every <if> and <else-if> branch.",
    ),
    IssueDefinition(
        code=IssueCode.CONDITION_ELSE_DUPLICATE,
        name="CONDITION_ELSE_DUPLICATE",
        title="Condition Else Duplicate",
        template="Fail while parsing <condition>. There can only be one tag <else> at most.",
        cause="A <condition> block contains more than one unconditional <else> fallback branch.",
        resolution="Keep at most one <else>, after all <if> and <else-if> branches.",
    ),
    IssueDefinition(
        code=IssueCode.CONDITION_INVALID_TAG,
        name="CONDITION_INVALID_TAG",
        title="Condition Invalid Tag",
        template="Invalid tag {tag} in <condition>.",
        cause=("The branch container accepts only <if>, <else-if>, and optional final <else> children."),
        resolution="Replace <{tag}> with a supported branch element or move it inside an existing branch.",
    ),
    IssueDefinition(
        code=IssueCode.CONDITION_NOT_BOOLEAN,
        name="CONDITION_NOT_BOOLEAN",
        title="Condition Not Boolean",
        template=(
            "Condition '{condition}' for {element_label} evaluated to a non-boolean value (not a "
            "valid boolean value): {value}"
        ),
        cause="A condition evaluated to a non-boolean value in the condition configuration.",
        resolution="Ensure the expression evaluates to true or false.",
    ),
]
