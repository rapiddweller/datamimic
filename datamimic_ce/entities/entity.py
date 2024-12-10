# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC


class Entity(ABC):  # noqa: B024
    def __init__(self, locale: str | None, dataset: str | None):
        self._locale = None if locale is None else locale.split("_")[0]
        self._dataset = dataset
