# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.authoring.rules import best_practice, cross_statement, intent_rules, schema_rules, semantic_rules
from datamimic_ce.authoring.rules.base import IntentLintContext, IntentRule, LintContext, Rule

ALL_RULES: tuple[type[Rule], ...] = (
    *schema_rules.RULES,
    *semantic_rules.RULES,
    *best_practice.RULES,
    *cross_statement.RULES,
)
ALL_INTENT_RULES: tuple[type[IntentRule], ...] = intent_rules.RULES

__all__ = ["ALL_INTENT_RULES", "ALL_RULES", "IntentLintContext", "IntentRule", "LintContext", "Rule"]
