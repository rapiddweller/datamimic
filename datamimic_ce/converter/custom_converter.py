# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class CustomConverter(Converter):
    def __init__(self, ctx: Any = None):
        self._ctx = ctx

    def convert(self, value) -> Any:
        pass
