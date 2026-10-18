# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.STATE_MACHINE_NO_TRANSITIONS,
        name="STATE_MACHINE_NO_TRANSITIONS",
        title="State Machine No Transitions",
        template="<state-machine '{id}'> must declare at least one <transition> child",
        cause="A <state-machine> element has zero <transition> children.",
        resolution="Add at least one <transition from= to=> child.",
    ),
]
