# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class IntegerGenerator:
    def __init__(self, class_factory_util: BaseClassFactoryUtil, min: int = 0, max: int = 1000000) -> None:
        if min > max:
            raise ValueError(f"Failed when init IntegerGenerator because min({min}) > max({max})")
        self._min = min
        self._max = max
        self._class_factory_util = class_factory_util

    def generate(self) -> int:
        return self._class_factory_util.get_data_generation_util().rnd_int(self._min, self._max)
