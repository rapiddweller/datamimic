# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.statements.composite_statement import CompositeStatement


class MappingStatement(CompositeStatement):
    def __init__(self, parent_stmt: CompositeStatement):
        super().__init__(None, parent_stmt=parent_stmt)
