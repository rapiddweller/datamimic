# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from abc import ABC
from typing import TypeVar, Generic, Type
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domain_core.base_entity import BaseEntity

T = TypeVar("T", bound=BaseEntity)
class BaseDomainService(ABC, Generic[T]):
    """
    Base class for all domain services.
    """
    def __init__(self, data_generator: BaseDomainGenerator, model_cls: Type[T]):
        self._data_generator = data_generator
        self._model_cls = model_cls

    def generate(self) -> T:
        """
        Generate a single instance of the domain object.
        :return:
        """
        return self._model_cls(self._data_generator)
    

    def generate_batch(self, count: int = 10) -> list[T]:
        """
        Generate a batch of data
        :param count:
        :return:
        """
        return [self.generate() for _ in range(count)]