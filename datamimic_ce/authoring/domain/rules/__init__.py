# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datamimic_ce.authoring.domain.rules.best_practice as best_practice
import datamimic_ce.authoring.domain.rules.cross_statement as cross_statement
import datamimic_ce.authoring.domain.rules.schema_rules as schema_rules
import datamimic_ce.authoring.domain.rules.semantic_rules as semantic_rules
from datamimic_ce.authoring.domain.rules.base import LintContext, Rule

ALL_RULES: tuple[type[Rule], ...] = (
    *schema_rules.RULES,
    *semantic_rules.RULES,
    *best_practice.RULES,
    *cross_statement.RULES,
)

__all__ = ["ALL_RULES", "LintContext", "Rule"]
