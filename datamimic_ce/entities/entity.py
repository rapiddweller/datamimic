# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from abc import ABC


class Entity(ABC):  # noqa: B024
    def __init__(self, locale: str | None, dataset: str | None):
        self._locale = None if locale is None else locale.split("_")[0]
        self._dataset = dataset
