# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.model.rule_model import RuleModel
from datamimic_ce.statements.statement import Statement


class RuleStatement(Statement):
    def __init__(self, model: RuleModel):
        super().__init__(None, None)
        self._if_rule = model.if_rule
        self._then_rule = model.then_rule

    @property
    def if_rule(self):
        return self._if_rule

    @property
    def then_rule(self):
        return self._then_rule
