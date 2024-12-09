# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
