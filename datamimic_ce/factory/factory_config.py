# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


class FactoryConfig:
    def __init__(self, entity_name: str, count: int, custom_data: dict):
        self._entity_name = entity_name
        self._count = count
        self._custom_data = custom_data

    @property
    def entity_name(self):
        return self._entity_name

    @property
    def count(self):
        return self._count

    @property
    def custom_data(self):
        return self._custom_data
