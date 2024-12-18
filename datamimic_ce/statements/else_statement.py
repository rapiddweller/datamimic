# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.else_model import ElseModel
from datamimic_ce.statements.composite_statement import CompositeStatement


class ElseStatement(CompositeStatement):
    def __init__(self, model: ElseModel, parent_stmt: CompositeStatement):
        super().__init__(name=None, parent_stmt=parent_stmt)
