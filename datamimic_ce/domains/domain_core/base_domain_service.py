# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from typing import Generic, TypeVar

from datamimic_ce.domains.domain_core.attribute_catalog import FieldSpec
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.domain_core.base_entity import BaseEntity
from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

T = TypeVar("T", bound=BaseEntity)


class BaseDomainService(ABC, Generic[T]):
    """
    Base service class for domain operations.

    This class provides the interface and common functionality for domain-specific
    services that generate and manipulate domain entities.

    Subclasses are discovered by name through the entity registry. The DSL-facing
    name is derived from the class name (``PersonService`` -> ``Person``).
    ``attribute_specs`` declares the fields the entity exposes so the registry can
    introspect it.
    """

    # Dataset-file glob patterns (with a ``{CC}`` placeholder) required by this
    # entity; override per service. Empty => supported_datasets() returns set().
    DATASET_PATTERNS: tuple[str, ...] = ()

    def __init__(self, data_generator: BaseDomainGenerator, model_cls: type[T]):
        self._data_generator = data_generator
        self._model_cls = model_cls

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        """Return the schema fields this entity exposes. Override per service."""
        return ()

    @classmethod
    def supported_datasets(cls) -> set[str]:
        """Return ISO dataset codes supported by all required datasets for this domain."""
        return compute_supported_datasets(cls.DATASET_PATTERNS)

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
